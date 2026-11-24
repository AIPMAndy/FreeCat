from pathlib import Path
import os
from playwright.sync_api import sync_playwright

source = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")
# Expose read-only test probes in memory only; the deployed page has no debug API.
anchor = "updateLang();rebuild();requestAnimationFrame(frame);"
assert source.count(anchor) == 1
probe = """window.__fc={get eye(){return eyeOpen},get pet(){return petting},get point(){return [tx,ty,scale,breath]},stats(x,y){const all=[...furGrid.values()].flat(),near=[...nearbyHair(x,y)],within=h=>(h.x-x)**2+(h.y-y)**2<=4200;return [all.length,near.length,all.filter(within).length,near.filter(within).length]}};"""
source = source.replace(anchor, probe + anchor, 1)
with sync_playwright() as p:
    options = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
    if os.getenv("CHROMIUM_PATH"):
        options["executable_path"] = os.environ["CHROMIUM_PATH"]
    browser = p.chromium.launch(**options)
    for w, h in [(1440, 920), (390, 844), (320, 640)]:
        page = browser.new_page(viewport={"width": w, "height": h}, locale="zh-CN", has_touch=w<500, is_mobile=w<500, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.set_content(source)
        page.wait_for_timeout(700)
        stats = page.evaluate("[[268,150],[310,330],[450,340],[230,445]].map(([x,y])=>__fc.stats(x,y))")
        assert all(a[2] == a[3] and a[1] < a[0] for a in stats), stats
        def pet(x, y):
            rect = page.locator("#cat").bounding_box()
            tx, ty, scale, breath = page.evaluate("__fc.point")
            X, Y = rect["x"]+tx+x*scale, rect["y"]+ty+y*scale*breath
            if w < 500:
                page.touchscreen.tap(X, Y)
            else:
                page.mouse.move(X, Y)
                page.mouse.down()
                page.mouse.up()
        pet(310, 150)
        page.wait_for_timeout(700)
        assert page.evaluate("__fc.pet && __fc.eye<.08")
        page.wait_for_timeout(1000)
        pet(310, 330)
        page.wait_for_timeout(650)
        assert .12 < page.evaluate("__fc.eye") < .32
        for i in range(8):
            button = page.locator("#palette button").nth(i)
            button.click()
            assert button.get_attribute("aria-pressed") == "true"
        page.locator("#cat").focus()
        page.keyboard.press("Space")
        page.wait_for_timeout(100)
        assert page.evaluate("__fc.pet")
        assert not errors, errors
        print(w, stats, "pass")
        page.close()
    page = browser.new_page(viewport={"width":390,"height":844}, locale="zh-CN", reduced_motion="reduce")
    page.set_content(source)
    page.wait_for_timeout(350)
    assert page.evaluate("__fc.eye") == 0
    page.locator("#cat").focus()
    page.keyboard.press("Space")
    page.wait_for_timeout(100)
    assert page.evaluate("__fc.pet && __fc.eye===0")
    page.close()
    browser.close()
