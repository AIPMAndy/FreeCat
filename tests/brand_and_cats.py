"""FreeCat room: bundled brand assets, real full-body cat photos, circular swatches and labeled AI virtual cats."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import mimetypes, os, base64

ROOT = Path(__file__).resolve().parents[1]
OUT = os.environ.get('FREECAT_SCREENSHOTS')
SOURCE = (ROOT / 'room.html').read_text()

def uri(path):
    f = ROOT / path
    mime = mimetypes.guess_type(f.name)[0] or ('image/webp' if f.suffix == '.webp' else 'application/octet-stream')
    return 'data:' + mime + ';base64,' + base64.b64encode(f.read_bytes()).decode()

ASSETS = (
    'assets/freecat.svg', 'assets/favicon-32.png', 'assets/apple-touch-icon.png', 'assets/social-card.jpg',
    'assets/cats/milo-tabby.webp', 'assets/cats/linen-tabby.webp', 'assets/cats/siamese-curl.webp',
    'assets/cats/thumb-milo-tabby.webp', 'assets/cats/thumb-linen-tabby.webp', 'assets/cats/thumb-siamese-curl.webp',
    'assets/cats/thumb-sleepy-tabby.webp', 'assets/cats/thumb-ginger.webp',
    'experiments/sleepy-tabby.webp', 'experiments/ginger.webp',
)
for path in ASSETS:
    assert (ROOT / path).is_file(), path

HTML = SOURCE.replace('src="assets/freecat.svg"', 'src="' + uri('assets/freecat.svg') + '"')
for path in ASSETS[4:]:
    HTML = HTML.replace(path, uri(path))

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None, args=['--no-sandbox'])
    for w, h in [(1440, 900), (390, 844), (320, 720)]:
        page = b.new_page(viewport={'width': w, 'height': h}, locale='zh-CN', device_scale_factor=1, reduced_motion='reduce', has_touch=w < 600, is_mobile=w < 600)
        errors, missing = [], []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('response', lambda r: missing.append(r.url) if r.status >= 400 else None)
        page.route('https://**/*', lambda route: route.abort())
        page.set_content(HTML)
        page.wait_for_function('!!mask && selectedCat===PHOTO_CAT && image.width===1024')
        assert page.evaluate('loadId===1'), 'only default full photo loaded before explicit switch'
        assert page.locator('#catSwatches button').count() == 5
        page.locator('#catSwatches button').nth(3).click()
        page.wait_for_function('selectedCat===3 && image.height>image.width')
        page.evaluate('soundMuted=true')
        page.wait_for_function('document.querySelector(".brand-icon").naturalWidth>0')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert page.locator('#nextCat').inner_text() == '换只猫'
        assert page.locator('link[rel="apple-touch-icon"]').get_attribute('href') == 'assets/apple-touch-icon.png'
        assert page.evaluate('loadId===2')
        assert 'AI' in page.locator('#photoCredit').inner_text()
        if OUT:
            Path(OUT).mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(Path(OUT) / f'portrait-{w}.png'))
        assert page.evaluate('hit([.55,.5])')
        assert not errors and not missing, (errors, missing)
        print(f'{w}: brand, 5 swatches, lazy full photo load, AI label OK', flush=True)
        page.close()
    b.close()
