from pathlib import Path
from playwright.sync_api import sync_playwright
import json, base64, os

ROOT = Path(__file__).resolve().parents[1]
source = Path(os.environ.get('FREECAT_ROOM', ROOT / 'room.html')).read_text()
def uri(path, mime='image/webp'): return 'data:' + mime + ';base64,' + base64.b64encode((ROOT / path).read_bytes()).decode()

html = source.replace('assets/freecat.svg', uri('assets/freecat.svg', 'image/svg+xml'))
for rel in (
    'assets/cats/milo-tabby.webp', 'assets/cats/linen-tabby.webp', 'assets/cats/siamese-curl.webp',
    'assets/cats/thumb-milo-tabby.webp', 'assets/cats/thumb-linen-tabby.webp', 'assets/cats/thumb-siamese-curl.webp',
    'assets/cats/thumb-sleepy-tabby.webp', 'assets/cats/thumb-ginger.webp',
    'experiments/sleepy-tabby.webp', 'experiments/ginger.webp',
):
    html = html.replace(rel, uri(rel))
assert html != source
OUTPUT = os.environ.get('FREECAT_SCREENSHOTS')
if OUTPUT: Path(OUTPUT).mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None, args=['--no-sandbox'])
    for w, h in [(1440, 900), (390, 844), (320, 720)]:
        page = b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=1, locale='zh-CN', reduced_motion='reduce', has_touch=w < 600, is_mobile=w < 600)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.set_content(html)
        page.locator('#cat').wait_for(state='visible')
        page.wait_for_function('!!mask && !cv.hidden && box[2]>0 && box[3]>0 && cv.width>1')
        page.wait_for_function('selectedCat===PHOTO_CAT && raf===0')
        page.evaluate('soundMuted=true')
        if OUTPUT: page.screenshot(path=str(Path(OUTPUT) / f'after-{w}.png'))
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        h1_id = '#mobileHeadline' if w <= 680 else '#headline'
        assert page.locator(h1_id).inner_text() == '来，摸一会儿猫。'
        assert page.locator('#status').inner_text() == '可以开始抚摸'
        canvas = page.locator('#cat')
        r = canvas.bounding_box()
        x, y = page.evaluate('()=>{const r=cv.getBoundingClientRect();return [r.left+r.width*(box[0]+point[0]*box[2]),r.top+r.height*(box[1]+point[1]*box[3])]}')
        assert page.evaluate('hit(point)')
        page.mouse.move(x, y); page.mouse.down(); page.mouse.move(x + 16, y + 5, steps=4); page.wait_for_timeout(120)
        assert page.evaluate('pressed && strength>.2')
        page.mouse.up()
        canvas.focus(); page.keyboard.down('Space'); page.wait_for_function('pressed'); page.keyboard.up('Space'); page.wait_for_function('!pressed')
        if w == 390:
            cdp = page.context.new_cdp_session(page)
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x + 12, 'y': y + 4}]})
            page.wait_for_function('pressed && strength>.2')
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
            page.wait_for_function('!pressed')
        page.locator('#sound').click()
        page.wait_for_function("audio && audio.state==='running' && soundButton.getAttribute('aria-pressed')==='true'")
        canvas.focus(); page.keyboard.down('Space'); page.wait_for_function('purring && purrGain.gain.value>.005')
        page.keyboard.up('Space'); page.wait_for_function('!purring && purrGain.gain.value<.002')
        page.locator('#sound').click(); assert page.evaluate('audio===null')
        page.locator('#night').click(); assert page.locator('body').evaluate("el=>el.classList.contains('night')")
        if OUTPUT: page.screenshot(path=str(Path(OUTPUT) / f'night-{w}.png'))
        page.locator('#language').click()
        assert page.locator(h1_id).inner_text() == 'Stay a little.'
        assert page.locator('#status').inner_text() == 'Ready to pet'
        page.locator('summary').click(); page.locator('#defaultCat').click()
        page.wait_for_function('!!mask && !failed')
        assert not page.locator('#options').evaluate('el=>el.open')
        assert page.locator('.nav a').evaluate_all('els=>els.map(e=>e.getAttribute("href"))') == [
            'index.html#discover', 'index.html#identify', 'index.html#collection', 'index.html#care', 'index.html#play'
        ]
        assert not errors, errors
        print(json.dumps({'width': w, 'canvas': r, 'scroll_height': page.evaluate('document.documentElement.scrollHeight'), 'errors': errors}, ensure_ascii=False), flush=True)
        page.close()
    b.close()
