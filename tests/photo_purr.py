"""Photo Lab: optional audio lifecycle and mobile cat coverage (Chromium)."""
import base64
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'experiments/photo-pet.html').read_text()
data = base64.b64encode((ROOT / 'experiments/ginger.webp').read_bytes()).decode()
html = source.replace("load('ginger.webp')", "load('data:image/webp;base64," + data + "')")
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None, args=['--no-sandbox'])
    for width, height in [(1440, 900), (390, 844), (320, 720)]:
        page = browser.new_page(viewport={'width': width, 'height': height}, device_scale_factor=1, reduced_motion='reduce', has_touch=width<600, is_mobile=width<600)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.set_content(html)
        canvas = page.locator('#cat')
        canvas.wait_for(state='visible')
        page.wait_for_function('!!mask && box[2]>0.5')
        sound = page.locator('#sound')
        assert sound.get_attribute('aria-pressed') == 'false'
        assert page.evaluate('audio===null && !purring')
        if width < 600:
            assert page.evaluate('box[2]>=.97 && cv.clientWidth/cv.clientHeight>=1.49')
        sound.click()
        page.wait_for_function("soundButton.getAttribute('aria-pressed')==='true' && audio.state==='running'")
        assert page.evaluate('!purring && purrGain.gain.value===0')
        rect = canvas.bounding_box()
        x,y = rect['x']+rect['width']*.55,rect['y']+rect['height']*.5
        page.mouse.move(x,y)
        page.mouse.down()
        page.wait_for_function('purring && purrGain.gain.value>.005')
        page.mouse.up()
        page.wait_for_function('!purring && purrGain.gain.value<.002')
        canvas.focus()
        page.keyboard.down('Space')
        page.wait_for_function('purring')
        page.locator('#reset').focus()
        page.wait_for_function('!purring')
        page.keyboard.up('Space')
        if width == 390:
            cdp = page.context.new_cdp_session(page)
            cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
            page.wait_for_function('purring')
            cdp.send('Input.dispatchTouchEvent', {'type':'touchCancel','touchPoints':[]})
            page.wait_for_function('!purring')
        canvas.focus()
        page.keyboard.down('Space')
        page.wait_for_function('purring')
        page.evaluate('stop()')
        page.wait_for_function('!purring')
        page.keyboard.up('Space')
        sound.click()
        assert page.evaluate('audio===null && !purring')
        assert sound.get_attribute('aria-pressed') == 'false'
        assert not errors, errors
        print(f'{width}px: silent default, opt-in, stroke/release, blur, stop, off; image width {page.evaluate("box[2]"):.3f}')
        page.close()
    browser.close()
