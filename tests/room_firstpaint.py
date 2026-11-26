"""In-memory Chromium regression: default full-body first paint, masked idle breathing and upload bounds."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import base64, json, os

ROOT = Path(__file__).resolve().parents[1]
OUT = os.environ.get('FREECAT_SCREENSHOTS')
if OUT: Path(OUT).mkdir(parents=True, exist_ok=True)
def uri(path, mime='image/webp'): return 'data:' + mime + ';base64,' + base64.b64encode((ROOT / path).read_bytes()).decode()

def inline_html(path):
    s = path.read_text().replace('assets/freecat.svg', uri('assets/freecat.svg', 'image/svg+xml'))
    for rel in (
        'assets/cats/milo-tabby.webp', 'assets/cats/linen-tabby.webp', 'assets/cats/siamese-curl.webp',
        'assets/cats/thumb-milo-tabby.webp', 'assets/cats/thumb-linen-tabby.webp', 'assets/cats/thumb-siamese-curl.webp',
        'assets/cats/thumb-sleepy-tabby.webp', 'assets/cats/thumb-ginger.webp',
        'experiments/sleepy-tabby.webp', 'experiments/ginger.webp',
    ):
        s = s.replace(rel, uri(rel))
    return s

SAMPLE = '''()=>{
    if (rendererMode !== 'webgl' || !gl) return {face: 0, torso: 100, sofa: 0, total: 100};
    const snap = t => {
        stop(); drawWebGL(t);
        const buf = new Uint8Array(cv.width * cv.height * 4);
        gl.readPixels(0, 0, cv.width, cv.height, gl.RGBA, gl.UNSIGNED_BYTE, buf);
        return buf;
    };
    const a = snap(0), b = snap(700 * Math.PI);
    const fp = CATS[0].faceProtect;
    let face = 0, torso = 0, sofa = 0, total = 0;
    for (let y = 0; y < cv.height; y += 2) for (let x = 0; x < cv.width; x += 2) {
        const i = ((cv.height - 1 - y) * cv.width + x) * 4;
        if (Math.abs(a[i]-b[i]) + Math.abs(a[i+1]-b[i+1]) + Math.abs(a[i+2]-b[i+2]) <= 4) continue;
        total++;
        const u = x / cv.width, v = y / cv.height;
        if (v < 0.16 || v > 0.88) sofa++;
        else if (Math.hypot((u - fp[0]) / fp[2], (v - fp[1]) / fp[3]) < 0.40) face++;
        else torso++;
    }
    wake();
    return {face, torso, sofa, total};
}'''

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None, args=['--no-sandbox'])
    doc = inline_html(ROOT / 'room.html')
    for w, h in [(1440, 900), (390, 844), (320, 720)]:
        static = b.new_page(viewport={'width': w, 'height': h}, java_script_enabled=False, has_touch=w < 600, is_mobile=w < 600, device_scale_factor=1)
        static.set_content(doc)
        assert static.locator('#preview').is_visible() and static.locator('#cat').is_hidden()
        assert static.locator('#preview').evaluate('el=>el.complete && el.naturalWidth===1024 && el.naturalHeight===1024')
        assert static.locator('noscript').inner_text().strip()
        if OUT: static.screenshot(path=str(Path(OUT) / f'firstpaint-{w}.png'))
        static.close()

        p = b.new_page(viewport={'width': w, 'height': h}, locale='zh-CN', has_touch=w < 600, is_mobile=w < 600, device_scale_factor=1, reduced_motion='no-preference')
        errors = []
        p.on('pageerror', lambda e: errors.append(str(e)))
        p.route('https://**/*', lambda route: route.abort())
        p.set_content(doc)
        p.wait_for_function('!!mask && selectedCat===PHOTO_CAT && !cv.hidden && hit(point)')
        assert p.locator('#preview').is_hidden()
        assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
        p.evaluate('soundMuted=true')

        r = p.evaluate(SAMPLE)
        assert r['face'] == 0 and r['sofa'] == 0 and r['torso'] > 20, r
        p.emulate_media(reduced_motion='reduce')
        p.wait_for_function('motion.matches')
        still = p.evaluate(SAMPLE)
        assert still['total'] == 0, still
        if OUT: p.screenshot(path=str(Path(OUT) / f'after-{w}.png'))
        assert p.evaluate('mask.w<=384 && mask.h<=384')

        # Fully transparent upload must not replace active cat.
        p.evaluate('''()=>{window.oldImage=image;const c=document.createElement('canvas');c.width=64;c.height=64;load(c.toDataURL())}''')
        p.wait_for_function("status.dataset.raw.includes('previous cat kept')")
        assert p.evaluate('image===window.oldImage && selectedCat===0 && hit(point)')

        # 1x1600 upload keeps mask bounded.
        p.evaluate('''()=>{const c=document.createElement('canvas');c.width=1;c.height=1600;const cc=c.getContext('2d');cc.fillStyle='#a76b42';cc.fillRect(0,0,1,1600);load(c.toDataURL())}''')
        p.wait_for_function('selectedCat===null && image.width===1')
        assert p.evaluate('mask.w===1 && mask.h===384 && hit(point)')
        p.locator('#cat').focus(); p.keyboard.down('Space'); p.wait_for_function('pressed'); p.keyboard.up('Space'); p.wait_for_function('!pressed')

        # Tiny isolated pixel is keyboard-reachable.
        p.evaluate('''()=>{const c=document.createElement('canvas');c.width=64;c.height=64;const cc=c.getContext('2d');cc.fillStyle='brown';cc.fillRect(11,13,1,1);load(c.toDataURL())}''')
        p.wait_for_function('image.width===64 && mask.w===64 && hit(point)')
        p.locator('#cat').focus(); p.keyboard.down('Space'); p.wait_for_function('pressed'); p.keyboard.up('Space'); p.wait_for_function('!pressed')

        p.locator('summary').click(); p.locator('#defaultCat').click()
        p.wait_for_function('selectedCat===PHOTO_CAT && hit(point)')
        assert not errors, errors
        print(json.dumps({'viewport': [w, h], 'motion': r, 'reduced_motion': still, 'errors': errors}), flush=True)
        p.close()
    b.close()
