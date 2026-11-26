from pathlib import Path
from playwright.sync_api import sync_playwright
import base64, json, os

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = os.environ.get('FREECAT_SCREENSHOTS')
if OUTPUT: Path(OUTPUT).mkdir(parents=True, exist_ok=True)
def uri(rel, mime='image/webp'): return 'data:' + mime + ';base64,' + base64.b64encode((ROOT / rel).read_bytes()).decode()

html = (ROOT / 'room.html').read_text().replace('assets/freecat.svg', uri('assets/freecat.svg', 'image/svg+xml'))
for rel in (
    'assets/cats/milo-tabby.webp', 'assets/cats/linen-tabby.webp', 'assets/cats/siamese-curl.webp',
    'assets/cats/thumb-milo-tabby.webp', 'assets/cats/thumb-linen-tabby.webp', 'assets/cats/thumb-siamese-curl.webp',
    'assets/cats/thumb-sleepy-tabby.webp', 'assets/cats/thumb-ginger.webp',
    'experiments/sleepy-tabby.webp', 'experiments/ginger.webp',
):
    html = html.replace(rel, uri(rel))

def coords(page, pt):
    return page.evaluate('p=>{const r=cv.getBoundingClientRect();return {x:r.left+r.width*(box[0]+p[0]*box[2]),y:r.top+r.height*(box[1]+p[1]*box[3])}}', pt)

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None, args=['--no-sandbox'])
    for w, h in [(1440, 900), (390, 844), (320, 720)]:
        for idx, name in [(0, 'milo'), (3, 'fluffy'), (4, 'ginger')]:
            p = b.new_page(viewport={'width': w, 'height': h}, locale='zh-CN', reduced_motion='reduce', has_touch=w < 600, is_mobile=w < 600, device_scale_factor=1)
            errors = []
            p.on('pageerror', lambda e: errors.append(str(e)))
            p.route('https://**/*', lambda route: route.abort())
            p.set_content(html)
            p.wait_for_function('!!mask && selectedCat===PHOTO_CAT && !cv.hidden')
            if idx != 0:
                p.locator('#catSwatches button').nth(idx).click()
                p.wait_for_function(f'selectedCat==={idx} && !!mask')
            p.evaluate('soundMuted=true'); p.wait_for_timeout(100)
            assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assert p.evaluate('hit(point)')
            assert p.locator('#status').inner_text() == '可以开始抚摸'
            if OUTPUT: p.screenshot(path=str(Path(OUTPUT) / f'{name}-{w}.png'))
            center = coords(p, p.evaluate('point'))
            outside = coords(p, [.05, .05])
            assert p.evaluate('!hit([.05,.05])')
            p.mouse.move(**center); p.mouse.down(); p.wait_for_function('pressed')
            p.mouse.move(center['x'] + 10, center['y'] + 8, steps=3)
            p.mouse.move(**outside); p.wait_for_function('!pressed && activeId!==null')
            p.mouse.move(**center); p.wait_for_function('pressed && activeId!==null')
            p.mouse.up(); p.wait_for_function('!pressed && activeId===null')
            p.locator('#cat').focus(); p.keyboard.down('Space'); p.wait_for_function('pressed'); p.keyboard.up('Space'); p.wait_for_function('!pressed')
            if w == 390:
                session = p.context.new_cdp_session(p)
                session.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [center]})
                p.wait_for_function('pressed')
                session.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [outside]})
                p.wait_for_function('!pressed && activeId!==null')
                session.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [center]})
                p.wait_for_function('pressed')
                session.send('Input.dispatchTouchEvent', {'type': 'touchCancel', 'touchPoints': []})
                p.wait_for_function('!pressed && activeId===null')
            p.locator('#sound').click(); p.wait_for_function("audio && audio.state==='running' && soundButton.getAttribute('aria-pressed')==='true'")
            p.locator('#cat').focus(); p.keyboard.down('Space'); p.wait_for_function('purring && purrGain.gain.value>.005')
            p.keyboard.up('Space'); p.wait_for_function('!purring')
            p.locator('#sound').click(); assert p.evaluate('audio===null')
            p.locator('#night').click(); assert p.evaluate("document.body.classList.contains('night')")
            p.locator('#language').click()
            h1_id = '#mobileHeadline' if w <= 680 else '#headline'
            assert p.locator(h1_id).inner_text() == 'Stay a little.'
            assert len(p.locator('.nav a').all()) == 5
            assert not errors, errors
            print(json.dumps(dict(w=w, asset=name, errors=errors)), flush=True)
            p.close()
    # Transparent center keyboard fixture
    p = b.new_page(viewport={'width': 390, 'height': 844}, reduced_motion='reduce')
    p.set_content(html)
    p.wait_for_function('!!mask')
    p.evaluate('''()=>{const c=document.createElement('canvas');c.width=200;c.height=200;const x=c.getContext('2d');x.fillStyle='brown';x.fillRect(12,12,36,36);load(c.toDataURL(),false,null)}''')
    p.wait_for_function('image.width===200 && !hit([.55,.5]) && hit(point)')
    p.locator('#cat').focus(); p.keyboard.down('Space'); p.wait_for_function('pressed'); p.keyboard.up('Space'); p.wait_for_function('!pressed')
    print('transparent-center keyboard passed', flush=True)
    p.close(); b.close()
