"""Real HTTP origin smoke test; uses exact checked-in media, not data URIs.
Run: python tests/served_room.py chromium (or webkit).
External recording is intentionally blocked; this tests synthesized fallback,
not the original recording, hardware speakers, physical devices or public Pages.
"""
import functools
import os
import sys
import threading
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ENGINE = sys.argv[1] if len(sys.argv) > 1 else "chromium"
OUT = Path(os.environ.get("FREECAT_SCREENSHOTS", "test-screens"))
OUT.mkdir(parents=True, exist_ok=True)
handler = functools.partial(SimpleHTTPRequestHandler, directory=str(ROOT))
server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
origin = f"http://127.0.0.1:{server.server_port}"
try:
    with sync_playwright() as pw:
        browser = getattr(pw, ENGINE).launch()
        for w, h in [(320,720), (390,844), (1440,900)]:
            context = browser.new_context(viewport={"width": w, "height": h}, locale="zh-CN",
                                          has_touch=w<600, is_mobile=w<600, device_scale_factor=1)
            context.route("https://**/*", lambda route: route.abort())
            page = context.new_page()
            errors, missing = [], []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("response", lambda r: missing.append(r.url) if r.url.startswith(origin) and r.status >= 400 else None)
            page.goto(origin + "/")
            page.wait_for_url("**/room.html")
            page.wait_for_function("!!mask && selectedCat===PHOTO_CAT && !cv.hidden && raf===0")
            assert page.evaluate("image.width===375 && image.height===300 && audio===null && !purring")
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
            assert "真实摄影" in page.locator("#photoCredit").inner_text()
            assert page.locator(".brand-icon").evaluate("e=>e.complete && e.naturalWidth>0")
            for path in ["assets/favicon-32.png", "assets/apple-touch-icon.png", "assets/social-card.jpg"]:
                response = context.request.get(origin+"/"+path)
                assert response.ok and response.headers["content-type"].startswith("image/"), path
            page.screenshot(path=str(OUT/f"{ENGINE}-{w}-initial.png"))
            page.locator("#cat").scroll_into_view_if_needed()
            x,y=page.evaluate("()=>{const r=cv.getBoundingClientRect();return [r.left+(box[0]+.45*box[2])*r.width,r.top+(box[1]+.48*box[3])*r.height]}")
            if w<600:
                page.touchscreen.tap(x,y)
            else:
                page.mouse.click(x,y)
            page.wait_for_function("audio && audio.state==='running' && purrGain.gain.value>.005")
            # Measure the first tap alone, before any second activating gesture.
            # In the old gate, the keyboard could conceal a failed initial audition.
            assert page.evaluate("!pressed && previewUntil > performance.now()")
            signal_js = """async()=>{const a=audio.createAnalyser();a.fftSize=2048;
                const silent=audio.createGain();silent.gain.value=0;
                purrGain.connect(a);a.connect(silent);silent.connect(audio.destination);
                await new Promise(r=>setTimeout(r,250));
                const buf=new Float32Array(a.fftSize);a.getFloatTimeDomainData(buf);
                const rms=Math.sqrt(buf.reduce((s,v)=>s+v*v,0)/buf.length);
                purrGain.disconnect(a);a.disconnect();silent.disconnect();return rms}"""
            first_tap_rms = page.evaluate(signal_js)
            assert first_tap_rms > 0.0005, ("first tap alone", ENGINE, w, first_tap_rms)
            page.wait_for_function("!purring && previewUntil===0")
            page.locator("#cat").focus()
            page.keyboard.down("Space")
            rms = page.evaluate(signal_js)
            assert rms>0.0005, rms
            page.screenshot(path=str(OUT/f"{ENGINE}-{w}-active.png"))
            page.keyboard.up("Space")
            page.wait_for_function("!pressed && raf===0")
            page.locator("#sound").click()
            assert page.evaluate("audio===null && soundMuted")
            page.reload()
            page.wait_for_function("!!mask && raf===0")
            assert page.evaluate("soundMuted && audio===null")
            page.locator("#cat").focus()
            page.keyboard.press("Space")
            assert page.evaluate("audio===null")
            page.locator("#sound").click()
            page.wait_for_function("audio && audio.state==='running' && purrGain.gain.value>.005")
            page.locator("#sound").click()
            page.locator("#nextCat").click();page.wait_for_function("selectedCat===0")
            page.locator("#nextCat").click();page.wait_for_function("selectedCat===1")
            page.locator("#nextCat").click();page.wait_for_function("selectedCat===PHOTO_CAT")
            page.locator("#language").click()
            assert "Real photograph" in page.locator("#photoCredit").inner_text()
            assert not errors and not missing, (errors,missing)
            print(ENGINE, w, "first tap RMS", first_tap_rms, "keyboard RMS", rms, "pass", flush=True)
            context.close()
        browser.close()
finally:
    server.shutdown()
    server.server_close()
