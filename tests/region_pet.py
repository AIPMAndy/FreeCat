"""Verify region-aware petting profiles across all curated cats (real photos + AI studio cats) and uploaded photos."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import os, base64, json

ROOT = Path(__file__).resolve().parents[1]
def uri(rel, mime='image/webp'): return 'data:' + mime + ';base64,' + base64.b64encode((ROOT / rel).read_bytes()).decode()

html = (ROOT / 'room.html').read_text().replace('assets/freecat.svg', uri('assets/freecat.svg', 'image/svg+xml'))
for rel in (
    'assets/cats/milo-tabby.webp', 'assets/cats/linen-tabby.webp', 'assets/cats/siamese-curl.webp',
    'assets/cats/thumb-milo-tabby.webp', 'assets/cats/thumb-linen-tabby.webp', 'assets/cats/thumb-siamese-curl.webp',
    'assets/cats/thumb-sleepy-tabby.webp', 'assets/cats/thumb-ginger.webp',
    'experiments/sleepy-tabby.webp', 'experiments/ginger.webp',
):
    html = html.replace(rel, uri(rel))

def pos(p, xy):
    return p.evaluate('xy=>{const r=cv.getBoundingClientRect();return {x:r.left+r.width*(box[0]+xy[0]*box[2]),y:r.top+r.height*(box[1]+xy[1]*box[3])}}', xy)

OUT = os.environ.get('FREECAT_SCREENSHOTS')
if OUT: Path(OUT).mkdir(parents=True, exist_ok=True)

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None, args=['--no-sandbox'])
    for w, h in [(1440, 900), (390, 844), (320, 720)]:
        p = b.new_page(viewport={'width': w, 'height': h}, locale='zh-CN', reduced_motion='reduce', device_scale_factor=1, has_touch=w < 600, is_mobile=w < 600)
        errors = []
        p.on('pageerror', lambda e: errors.append(str(e)))
        p.route('https://**/*', lambda route: route.abort())
        p.set_content(html)
        p.wait_for_function('!!mask && selectedCat===PHOTO_CAT && !cv.hidden')
        p.evaluate('soundMuted=true')
        assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')

        # Milo's anatomical regions: back has higher gain & radius than paws; every region hits.
        milo_prof = p.evaluate('''()=>({
            back: petProfile([.52,.39], 0),
            head: petProfile([.30,.49], 0),
            paws: petProfile([.37,.67], 0),
            allHit: CATS[0].regions.every(r => hit([r[1], r[2]]))
        })''')
        assert milo_prof['allHit'] and milo_prof['back']['gain'] > milo_prof['paws']['gain'], milo_prof
        assert milo_prof['back']['radius'] > milo_prof['paws']['radius'], milo_prof

        # Uploaded photo keeps generic profile (no assumed anatomy).
        assert p.evaluate('petProfile([.31,.24], null).radius===1 && petProfile([.31,.24], null).gain===1')

        # Active dragging across Milo's back updates status with region label & pauses over sofa gap.
        xy = pos(p, [.52, .39])
        sofa = pos(p, [.50, .08])
        assert not p.evaluate('hit([.50,.08])')
        p.mouse.move(**xy); p.mouse.down(); p.mouse.move(xy['x'] + 18, xy['y'] + 6, steps=5)
        p.wait_for_function('pressed && strength>.2')
        assert '背部' in p.locator('#status').inner_text()
        if OUT and w == 390: p.screenshot(path=str(Path(OUT) / 'after-active-390.png'))
        p.mouse.move(**sofa); p.wait_for_function('!pressed && activeId!==null')
        p.mouse.move(**xy); p.wait_for_function('pressed && activeId!==null')
        p.mouse.up(); p.wait_for_function('!pressed && activeId===null')

        # Verify uploaded photo resets to generic profile.
        p.locator('#file').set_input_files(str(ROOT / 'assets/cats/milo-tabby.webp'))
        p.wait_for_function('selectedCat===null')
        assert p.evaluate('petProfile([.31,.24]).radius===1')
        assert not errors, errors
        print(json.dumps({'viewport': [w, h], 'milo': milo_prof, 'errors': errors}), flush=True)
        p.close()
    b.close()
