"""Verify organic idle breathing & ear micro-twitch stay strictly inside body mask, honor reduced motion, and stop on uploads."""
from pathlib import Path
import base64, json, os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = os.environ.get('FREECAT_SCREENSHOTS')
if OUT: Path(OUT).mkdir(parents=True, exist_ok=True)
def uri(rel, mime='image/webp'): return 'data:' + mime + ';base64,' + base64.b64encode((ROOT / rel).read_bytes()).decode()

html = (ROOT / 'room.html').read_text().replace('assets/freecat.svg', uri('assets/freecat.svg', 'image/svg+xml'))
for rel in (
    'assets/cats/milo-tabby.webp', 'assets/cats/linen-tabby.webp', 'assets/cats/siamese-curl.webp',
    'assets/cats/thumb-milo-tabby.webp', 'assets/cats/thumb-linen-tabby.webp', 'assets/cats/thumb-siamese-curl.webp',
    'assets/cats/thumb-sleepy-tabby.webp', 'assets/cats/thumb-ginger.webp',
    'experiments/sleepy-tabby.webp', 'experiments/ginger.webp',
):
    html = html.replace(rel, uri(rel))

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None, args=['--no-sandbox'])
    for w, h in [(320, 720), (390, 844), (1440, 900)]:
        page = browser.new_page(viewport={'width': w, 'height': h}, device_scale_factor=1, locale='zh-CN', has_touch=w < 600, is_mobile=w < 600, reduced_motion='no-preference')
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.route('https://**/*', lambda route: route.abort())
        page.set_content(html)
        page.wait_for_function('!!mask && selectedCat===PHOTO_CAT && !cv.hidden && cv.width>1')
        page.evaluate('soundMuted=true')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')

        # Measure torso breathing and ear twitch isolation on Milo.
        metrics = page.evaluate('''()=>{
            if (rendererMode !== 'webgl' || !gl) return {mode: rendererMode, skipped: true};
            const snap = t => {
                stop(); drawWebGL(t);
                const buf = new Uint8Array(cv.width * cv.height * 4);
                gl.readPixels(0, 0, cv.width, cv.height, gl.RGBA, gl.UNSIGNED_BYTE, buf);
                return buf;
            };
            const compare = (t0, t1) => {
                const a = snap(t0), b = snap(t1);
                let changed = 0, sofa = 0, face = 0;
                const fp = CATS[0].faceProtect;
                for (let y = 0; y < cv.height; y += 2) for (let x = 0; x < cv.width; x += 2) {
                    const i = ((cv.height - 1 - y) * cv.width + x) * 4;
                    if (Math.abs(a[i]-b[i]) + Math.abs(a[i+1]-b[i+1]) + Math.abs(a[i+2]-b[i+2]) <= 3) continue;
                    changed++;
                    const u = x / cv.width, v = y / cv.height;
                    if (v < 0.16 || v > 0.88) sofa++;
                    if (Math.hypot((u - fp[0]) / fp[2], (v - fp[1]) / fp[3]) < 0.40) face++;
                }
                return {changed, sofa, face};
            };
            const breath = compare(0, 700 * Math.PI);
            const ear = compare(0, 8110); // 8110 + 1400 = 9510 -> inside 9400ms ear pulse window
            wake();
            return {mode: 'webgl', breath, ear};
        }''')
        if not metrics.get('skipped'):
            assert metrics['breath']['changed'] > 20 and metrics['breath']['sofa'] == 0 and metrics['breath']['face'] == 0, metrics
            assert metrics['ear']['changed'] > 10 and metrics['ear']['sofa'] == 0 and metrics['ear']['face'] == 0, metrics

        # Reduced motion halts idle animation completely.
        page.emulate_media(reduced_motion='reduce')
        page.wait_for_function('motion.matches && raf===0', timeout=4000)
        assert page.evaluate('''()=>{stop();if(rendererMode==='webgl'&&gl){drawWebGL(0);const a=cv.toDataURL();drawWebGL(2200);return a===cv.toDataURL()}return true}''')

        # Uploaded photos must never inherit anatomical idle animation.
        page.emulate_media(reduced_motion='no-preference')
        page.wait_for_function('!motion.matches')
        page.evaluate("load(CATS[0].src, false, null)")
        page.wait_for_function('selectedCat===null && raf===0')
        assert not errors, errors
        print(json.dumps({'width': w, **metrics, 'page_errors': errors}, ensure_ascii=False), flush=True)
        page.close()
    browser.close()
