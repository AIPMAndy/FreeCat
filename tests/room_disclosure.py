from pathlib import Path
from playwright.sync_api import sync_playwright
import base64, json, os

r = Path(__file__).resolve().parents[1]
out = os.environ.get("FREECAT_SCREENSHOTS")
if out: Path(out).mkdir(parents=True, exist_ok=True)
def uri(rel, mime='image/webp'): return 'data:' + mime + ';base64,' + base64.b64encode((r / rel).read_bytes()).decode()

html = (r / 'room.html').read_text().replace('assets/freecat.svg', uri('assets/freecat.svg', 'image/svg+xml'))
for rel in (
    'assets/cats/milo-tabby.webp', 'assets/cats/linen-tabby.webp', 'assets/cats/siamese-curl.webp',
    'assets/cats/thumb-milo-tabby.webp', 'assets/cats/thumb-linen-tabby.webp', 'assets/cats/thumb-siamese-curl.webp',
    'assets/cats/thumb-sleepy-tabby.webp', 'assets/cats/thumb-ginger.webp',
    'experiments/sleepy-tabby.webp', 'experiments/ginger.webp',
):
    html = html.replace(rel, uri(rel))

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None, args=['--no-sandbox'])
    for w, h in [(320, 720), (390, 844), (1440, 900)]:
        for loc in ['en-US', 'zh-CN']:
            page = b.new_page(viewport={'width': w, 'height': h}, locale=loc, reduced_motion='reduce', device_scale_factor=1, has_touch=w < 600, is_mobile=w < 600)
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.set_content(html)
            page.wait_for_function('!!mask && !cv.hidden && box[2]>0')
            if out: page.screenshot(path=str(Path(out) / f'closed-{w}-{loc}.png'), full_page=True)
            page.locator('summary').click()
            page.wait_for_function("document.querySelector('.options button').getBoundingClientRect().bottom<=innerHeight+1")
            if out: page.screenshot(path=str(Path(out) / f'after-{w}-{loc}.png'), full_page=True)
            metrics = page.evaluate('''()=>{const r=document.querySelector('.options').getBoundingClientRect(),n=document.querySelector('.primary-nav').getBoundingClientRect(),c=document.querySelector('.creator-bar').getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,navBottom:n.bottom,creatorTop:c.top,scrollWidth:document.documentElement.scrollWidth,innerWidth,scrollHeight:document.documentElement.scrollHeight}}''')
            assert metrics['left'] >= 0 and metrics['right'] <= w + 1 and metrics['top'] >= metrics['navBottom'] - 1 and metrics['bottom'] <= metrics['creatorTop'] + 1, metrics
            page.keyboard.press('Escape')
            assert not page.locator('#options').evaluate('e=>e.open')
            assert page.evaluate('document.activeElement===summary')
            page.locator('summary').click()
            page.locator('#nextCat').click()
            page.wait_for_function('selectedCat===1')
            assert not page.locator('#options').evaluate('e=>e.open')
            page.locator('summary').click()
            page.locator('#defaultCat').click()
            page.wait_for_function('selectedCat===PHOTO_CAT')
            assert page.evaluate('document.activeElement===summary')
            page.locator('#sound').click()
            page.wait_for_function("audio && audio.state==='running'")
            page.locator('#cat').scroll_into_view_if_needed()
            x, y = page.evaluate('()=>{const r=cv.getBoundingClientRect();return [r.left+r.width*(box[0]+point[0]*box[2]),r.top+r.height*(box[1]+point[1]*box[3])]}')
            page.mouse.move(x, y); page.mouse.down(button='right')
            assert page.evaluate('!pressed && activeId===null')
            page.mouse.up(button='right')
            page.mouse.down(); page.wait_for_function('pressed && activeId!==null')
            page.mouse.move(x + 12, y + 5, steps=3)
            page.wait_for_function('strength>.2 && purring && purrGain.gain.value>.005')
            page.evaluate("window.dispatchEvent(new Event('blur'))")
            assert page.evaluate('!pressed && activeId===null && !purring')
            page.wait_for_function('purrGain.gain.value<.002')
            page.mouse.up()
            page.mouse.move(x, y); page.mouse.down(); page.wait_for_function('pressed'); page.mouse.up()
            assert page.evaluate('!pressed && activeId===null')
            page.locator('#cat').focus(); page.keyboard.down('Space'); page.wait_for_function('pressed')
            page.evaluate("window.dispatchEvent(new Event('pagehide'))")
            assert page.evaluate('!pressed && activeId===null && raf===0')
            page.keyboard.up('Space')
            page.evaluate("window.dispatchEvent(new Event('pageshow'))")
            page.locator('#cat').focus(); page.keyboard.down('Space'); page.wait_for_function('pressed')
            page.keyboard.up('Space'); page.wait_for_function('!pressed')
            if w == 390:
                page.locator('#cat').scroll_into_view_if_needed()
                x, y = page.evaluate('()=>{const r=cv.getBoundingClientRect();return [r.left+r.width*(box[0]+point[0]*box[2]),r.top+r.height*(box[1]+point[1]*box[3])]}')
                cdp = page.context.new_cdp_session(page)
                cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
                page.wait_for_function('pressed && activeId!==null')
                cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x + 15, 'y': y + 5}]})
                page.wait_for_function('strength>.2')
                cdp.send('Input.dispatchTouchEvent', {'type': 'touchCancel', 'touchPoints': []})
                page.wait_for_function('!pressed && activeId===null')
            page.locator('#sound').click(); assert page.evaluate('audio===null')
            assert not errors, errors
            print(w, loc, json.dumps(metrics), 'pass', flush=True)
            page.close()
    b.close()
