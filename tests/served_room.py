"""Real HTTP origin smoke test; uses exact checked-in media, not data URIs.
Run: python tests/served_room.py chromium (or webkit).
External requests are blocked. Verifies exact local recording, full-body default photo,
background rejection, first-tap signal, recorded path, swatch switching, upload stillness and bilingual UI.
"""
import functools
import hashlib
import os
import sys
import threading
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
assert hashlib.sha256((ROOT / 'assets/ariadne-purr.mp3').read_bytes()).hexdigest() == '81a70e312dc1166cb22b8558202729cbefdcee5dfd6895badf4c80d13c440ae4'
assert hashlib.sha256((ROOT / 'assets/cats/milo-tabby.webp').read_bytes()).hexdigest() == '6df824046b3214167969e11218acd00dd9fb4e42aa1599700adf5732f30e2878'
ENGINE = sys.argv[1] if len(sys.argv) > 1 else "chromium"
OUT = Path(os.environ.get("FREECAT_SCREENSHOTS", "test-screens"))
OUT.mkdir(parents=True, exist_ok=True)
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
handler = functools.partial(QuietHandler, directory=str(ROOT))
server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
origin = f"http://localhost:{server.server_port}"
try:
    with sync_playwright() as pw:
        browser = getattr(pw, ENGINE).launch()
        for w, h in [(320,720), (390,844), (1440,900)]:
            context = browser.new_context(viewport={"width": w, "height": h}, locale="zh-CN",
                                          has_touch=w<600, is_mobile=w<600, device_scale_factor=1)
            context.route("https://**/*", lambda route: route.abort())
            page = context.new_page()
            errors, missing, media_requests = [], [], []
            page.on('request', lambda r: media_requests.append(r.url) if 'ariadne-purr.mp3' in r.url else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("response", lambda r: missing.append(r.url) if r.url.startswith(origin) and r.status >= 400 else None)
            page.goto(origin + "/")
            page.wait_for_url("**/room.html")
            page.wait_for_function("!!mask && selectedCat===PHOTO_CAT && !cv.hidden && cv.width>1")
            assert page.evaluate("image.width===1024 && image.height===1024 && audio===null && !purring")
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
            assert not media_requests, 'no pre-gesture audio fetch'
            assert "真实摄影" in page.locator("#photoCredit").inner_text()
            assert page.locator(".brand-icon").evaluate("e=>e.complete && e.naturalWidth>0")
            for path in ["assets/favicon-32.png", "assets/apple-touch-icon.png", "assets/social-card.jpg",
                         "assets/cats/milo-tabby.webp", "assets/cats/linen-tabby.webp", "assets/cats/siamese-curl.webp"]:
                response = context.request.get(origin+"/"+path)
                assert response.ok and response.headers["content-type"].startswith("image/"), path
            page.screenshot(path=str(OUT/f"{ENGINE}-{w}-initial.png"))
            page.locator("#cat").scroll_into_view_if_needed()
            # Tapping the stationary sofa background must NOT activate petting or audio.
            bgx, bgy = page.evaluate("()=>{const r=cv.getBoundingClientRect();return [r.left+r.width*.5, r.top+r.height*.08]}")
            if w < 600:
                page.touchscreen.tap(bgx, bgy)
            else:
                page.mouse.click(bgx, bgy)
            assert page.evaluate("audio===null && !purring")
            assert not media_requests, 'background tap must not request audio'
            # Tapping the cat's back activates audio and unlocks the bundled real purr recording.
            x, y = page.evaluate("()=>{const r=cv.getBoundingClientRect();return [r.left+(box[0]+.52*box[2])*r.width,r.top+(box[1]+.39*box[3])*r.height]}")
            if w < 600:
                page.touchscreen.tap(x, y)
            else:
                page.mouse.click(x, y)
            page.wait_for_function("audio && audio.state==='running' && purrGain.gain.value>.005")
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
            page.wait_for_function('recordingReady', timeout=8000)
            assert media_requests == [origin + '/assets/ariadne-purr.mp3'], media_requests
            assert '真实呼噜录音' in page.locator('#purrKind').text_content()
            page.locator("#cat").focus()
            page.keyboard.down("Space")
            rms = page.evaluate(signal_js)
            assert rms > 0.0005, rms
            page.screenshot(path=str(OUT/f"{ENGINE}-{w}-active.png"))
            page.keyboard.up("Space")
            page.wait_for_function("!pressed")
            page.locator("#sound").click()
            assert page.evaluate("audio===null && soundMuted")
            page.reload()
            page.wait_for_function("!!mask && cv.width>1")
            assert page.evaluate("soundMuted && audio===null")
            page.locator("#cat").focus()
            page.keyboard.press("Space")
            assert page.evaluate("audio===null")
            page.locator("#sound").click()
            page.wait_for_function("audio && audio.state==='running' && purrGain.gain.value>.005")
            page.locator("#sound").click()
            # Switch through all 5 curated cats (3 real photos + 2 labeled AI cats).
            for idx in (1, 2, 3, 4, 0):
                page.locator("#nextCat").click()
                page.wait_for_function(f"selectedCat==={idx} && !!mask")
                if idx in (3, 4):
                    assert "AI" in page.locator("#photoCredit").inner_text()
                else:
                    assert "真实摄影" in page.locator("#photoCredit").inner_text()
            # Uploaded local photo must remain completely still at rest (no forced idle loop).
            page.locator("#file").set_input_files(str(ROOT/"assets/cats/milo-tabby.webp"))
            page.wait_for_function("selectedCat===null && !!mask && raf===0")
            still = page.evaluate("cv.toDataURL()")
            page.wait_for_timeout(300)
            assert page.evaluate("raf===0") and still == page.evaluate("cv.toDataURL()")
            page.locator("#cat").focus()
            page.keyboard.down("ArrowLeft")
            page.wait_for_function("pressed && raf!==0")
            page.keyboard.up("ArrowLeft")
            page.wait_for_function("!pressed && raf===0", timeout=3500)
            page.evaluate("load(CATS[PHOTO_CAT].src,false,PHOTO_CAT)")
            page.wait_for_function("selectedCat===PHOTO_CAT")
            page.locator("#language").click()
            assert "Real photograph" in page.locator("#photoCredit").inner_text()
            assert not errors and not missing, (errors, missing)
            print(ENGINE, w, "mode", page.evaluate("rendererMode"), "first tap RMS", first_tap_rms, "recorded keyboard RMS", rms, "pass", flush=True)
            context.close()
        browser.close()
finally:
    server.shutdown()
    server.server_close()
