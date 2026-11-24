from pathlib import Path
import os
from playwright.sync_api import sync_playwright

source = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")
with sync_playwright() as p:
    options = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
    if os.getenv("CHROMIUM_PATH"):
        options["executable_path"] = os.environ["CHROMIUM_PATH"]
    browser = p.chromium.launch(**options)
    for w, h in [(1440, 920), (390, 844), (320, 640)]:
        page = browser.new_page(viewport={"width": w, "height": h}, locale="zh-CN", is_mobile=w < 500, has_touch=w < 500)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.set_content(source)
        page.wait_for_timeout(450)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert page.locator(".swatch").first.bounding_box()["width"] >= 44
        page.locator("#cat").focus()
        page.keyboard.press("Space")
        page.wait_for_timeout(100)
        assert "喜欢" in page.locator("#statusText").inner_text()
        page.locator("#theme").click()
        assert page.locator("body").evaluate("e=>e.classList.contains('dark')")
        page.locator("#theme").click()
        page.locator("#worldNav [data-page=discover]").click()
        assert page.locator("#breedGrid article").count() == 20
        page.locator("#breedSearch").fill("布偶")
        assert page.locator("#breedGrid article").count() == 1
        page.locator("#worldNav [data-page=identify]").click()
        page.select_option("[name=coat]", "long")
        page.select_option("[name=pattern]", "point")
        page.locator("#matchForm button").click()
        assert "布偶" in page.locator("#matchResults").inner_text()
        for n in ["collection", "care", "play", "pet"]:
            page.locator(f"#worldNav [data-page={n}]").click()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), n
        page.locator("#language").click()
        assert page.locator("#worldNav button").first.inner_text() == "Pet a cat"
        assert not errors, errors
        print(f"PASS {w}x{h}: navigation, keyboard pet, theme, atlas, trait matcher, language and layout")
        page.close()
    browser.close()
