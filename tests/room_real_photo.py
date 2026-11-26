"""Real full-body photographs, WebGL/2D background & face protection, first-touch purr fallback and switching."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import base64, os

ROOT = Path(__file__).resolve().parents[1]
def uri(path, mime): return 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode()

html = (ROOT / 'room.html').read_text()
for rel in (
    'assets/cats/milo-tabby.webp', 'assets/cats/linen-tabby.webp', 'assets/cats/siamese-curl.webp',
    'assets/cats/thumb-milo-tabby.webp', 'assets/cats/thumb-linen-tabby.webp', 'assets/cats/thumb-siamese-curl.webp',
    'assets/cats/thumb-sleepy-tabby.webp', 'assets/cats/thumb-ginger.webp',
    'experiments/sleepy-tabby.webp', 'experiments/ginger.webp',
):
    html = html.replace(rel, uri(ROOT / rel, 'image/webp'))
html = html.replace('assets/freecat.svg', uri(ROOT / 'assets/freecat.svg', 'image/svg+xml'))
html = html.replace('<head>', '<head><script>window.fetch=()=>Promise.reject(Error("recording unavailable fixture"));</script>', 1)

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None, args=['--no-sandbox', '--disable-dev-shm-usage'])
    for w, h in [(1440, 900), (390, 844), (320, 720)]:
        page = b.new_page(viewport={'width': w, 'height': h}, locale='zh-CN', device_scale_factor=1, has_touch=w < 600, is_mobile=w < 600, reduced_motion='no-preference')
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.set_content(html)
        page.wait_for_function('!!mask && selectedCat===PHOTO_CAT && cv.width>1')
        assert page.evaluate('image.width===1024 && image.height===1024 && audio===null && !purring')
        # Verify background sofa pixels and protected eye/nose core remain untouched while back fur moves.
        isolation = page.evaluate('''()=>{
            const read = () => {
                if (rendererMode === 'webgl' && gl) {
                    const buf = new Uint8Array(cv.width * cv.height * 4);
                    gl.readPixels(0, 0, cv.width, cv.height, gl.RGBA, gl.UNSIGNED_BYTE, buf);
                    return {data: buf, flip: true};
                }
                return {data: ctx.getImageData(0, 0, cv.width, cv.height).data, flip: false};
            };
            stop();
            if (rendererMode === 'webgl' && gl) drawWebGL(0); else draw2D(0);
            const a = read();
            point = [.52, .39]; delta = [.04, .015]; strength = 1;
            if (rendererMode === 'webgl' && gl) drawWebGL(1200); else draw2D(1200);
            const b = read();
            let bodyMoved = 0, sofaMoved = 0, faceCoreMoved = 0;
            const fp = CATS[0].faceProtect;
            for (let y = 0; y < cv.height; y += 2) for (let x = 0; x < cv.width; x += 2) {
                const ry = a.flip ? (cv.height - 1 - y) : y;
                const i = (ry * cv.width + x) * 4;
                if (Math.abs(a.data[i]-b.data[i]) + Math.abs(a.data[i+1]-b.data[i+1]) + Math.abs(a.data[i+2]-b.data[i+2]) <= 3) continue;
                const u = x / cv.width, v = y / cv.height;
                if (v < 0.16 || v > 0.88) sofaMoved++;
                else if (Math.hypot((u - fp[0]) / fp[2], (v - fp[1]) / fp[3]) < 0.40) faceCoreMoved++;
                else bodyMoved++;
            }
            strength = 0; delta = [0, 0]; wake();
            return {mode: rendererMode, bodyMoved, sofaMoved, faceCoreMoved};
        }''')
        assert isolation['sofaMoved'] == 0 and isolation['faceCoreMoved'] == 0 and isolation['bodyMoved'] > 80, isolation
        assert '真实摄影' in page.locator('#photoCredit').inner_text()
        assert page.locator('#photoSource').is_visible()
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')

        # Background click rejected; cat back drag activates synthetic purr fallback cleanly.
        assert not page.evaluate('hit([.5, .08])')
        assert page.evaluate('hit([.52, .39])')
        x, y = page.evaluate('()=>{const r=cv.getBoundingClientRect();return [r.left+r.width*.52, r.top+r.height*.39]}')
        page.mouse.move(x, y); page.mouse.down()
        page.wait_for_function("audio && audio.state==='running' && purring && purrGain.gain.value>.08")
        assert '背部' in page.locator('#status').inner_text()
        levels = page.evaluate('''()=>{const a=makePurrBuffer(audio).getChannelData(0);let sq=0,peak=0;for(let i=0;i<a.length;i++){sq+=a[i]*a[i];peak=Math.max(peak,Math.abs(a[i]))}return {rms:Math.sqrt(sq/a.length),peak}}''')
        assert .02 < levels['rms'] < .3 and levels['peak'] < .8, levels
        page.mouse.move(x + 36, y + 10, steps=3); page.wait_for_timeout(90)
        assert page.evaluate('trail.length>=1 && trail.length<=TRAIL_LIMIT')
        page.mouse.up()
        page.wait_for_function('!purring && purrGain.gain.value<.02', timeout=4000)

        # Reduced motion halts idle loop completely.
        page.emulate_media(reduced_motion='reduce')
        page.wait_for_function('motion.matches && raf===0', timeout=4000)

        # Mute, switch through real + AI cats, check honest AI labeling and English switch.
        page.locator('#sound').click(); assert page.evaluate('audio===null && soundMuted')
        page.mouse.move(x, y); page.mouse.down(); page.mouse.up(); page.wait_for_timeout(120)
        assert page.evaluate('audio===null')
        page.locator('#sound').click(); page.wait_for_function('audio && purring && purrGain.gain.value>.05')
        page.wait_for_function('!purring && purrGain.gain.value<.02', timeout=4000)

        page.locator('#catSwatches button').nth(3).click()
        page.wait_for_function('selectedCat===3'); assert 'AI' in page.locator('#photoCredit').inner_text()
        page.locator('#catSwatches button').nth(1).click()
        page.wait_for_function('selectedCat===1'); assert '真实摄影' in page.locator('#photoCredit').inner_text()
        page.locator('#catSwatches button').nth(0).click()
        page.wait_for_function('selectedCat===0')
        page.locator('#language').click(); assert 'Real photograph' in page.locator('#photoCredit').inner_text()
        assert not errors, errors
        print(f'{w}: real full-body photo, isolation={isolation}, fallback={levels}', flush=True)
        page.close()
    b.close()
