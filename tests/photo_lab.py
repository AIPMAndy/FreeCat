"""Isolated photo renderer regression; supply an original transparent cat WebP.

FREECAT_PHOTO=/path/to/ginger.webp CHROMIUM_PATH=/usr/bin/chromium python tests/photo_lab.py
Uses an in-memory data URI because file navigation may be restricted in CI.
"""
import base64
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ASSET = Path(os.environ.get('FREECAT_PHOTO', ROOT / 'experiments/ginger.webp'))
SOURCE = (ROOT / 'experiments/photo-pet.html').read_text(encoding='utf-8')
assert ASSET.is_file(), 'Provide FREECAT_PHOTO: the original transparent ginger WebP sample.'
DATA = 'data:image/webp;base64,' + base64.b64encode(ASSET.read_bytes()).decode()
HTML = SOURCE.replace("load('ginger.webp')", f"load('{DATA}')")
assert HTML != SOURCE

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None, args=['--no-sandbox'])
    for width, height in [(1440, 900), (390, 844), (320, 720)]:
        page = browser.new_page(viewport={'width': width, 'height': height}, reduced_motion='reduce', has_touch=width < 600, is_mobile=width < 600, device_scale_factor=1)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.set_content(HTML)
        canvas = page.locator('#cat')
        canvas.wait_for(state='visible')
        page.wait_for_timeout(200)
        assert page.evaluate('!!ctx && !failed && !!mask')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert page.evaluate('!hit([0,0]) && hit([.55,.5])')
        before = page.evaluate('cv.toDataURL()')
        rect = canvas.bounding_box()
        x, y = rect['x'] + rect['width'] * .55, rect['y'] + rect['height'] * .5
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x + 20, y + 8, steps=3)
        page.wait_for_timeout(110)
        assert page.evaluate('pressed && strength>.2 && Math.abs(delta[0])>0')
        assert before != page.evaluate('cv.toDataURL()'), 'Stroke must change rendered pixels'
        page.mouse.up()
        page.wait_for_timeout(600)
        assert page.evaluate('!pressed && strength<.02')
        canvas.focus()
        page.keyboard.down('Space')
        page.wait_for_timeout(180)
        assert page.evaluate('pressed && strength>.2')
        page.keyboard.up('Space')
        page.wait_for_timeout(850)
        assert page.evaluate('!raf && !pressed')
        if width == 390:
            cdp = page.context.new_cdp_session(page)
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x + 18, 'y': y + 5}]})
            page.wait_for_timeout(140)
            assert page.evaluate('pressed && strength>.2 && delta[0]>0')
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
            page.wait_for_timeout(150)
            assert page.evaluate('!pressed && activeId===null')
        page.locator('#file').set_input_files(str(ASSET))
        page.wait_for_timeout(400)
        assert page.evaluate('image.width>0 && !failed')
        assert not errors, errors
        print(f'{width}px: render, stroke pixels, keyboard, local file, reduced motion passed')
        page.close()
    page = browser.new_page()
    page.evaluate("()=>{const g=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(t,...a){return this.id==='cat'?null:g.call(this,t,...a)}}")
    page.set_content(HTML)
    page.locator('#preview').wait_for(state='visible')
    assert 'Static preview' in page.locator('#status').inner_text()
    page.close()
    page = browser.new_page()
    page.set_content(SOURCE)
    page.wait_for_function("document.getElementById('status').textContent.includes('Sample unavailable')")
    page.locator('#file').set_input_files(str(ASSET))
    page.locator('#cat').wait_for(state='visible')
    assert page.evaluate('!failed && !!image')
    print('Missing asset recovery and unavailable renderer fallback passed')
    browser.close()
