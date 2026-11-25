"""Atlas provenance, local-journal isolation and image loading/fallback tests.
Network images are intercepted with a tiny non-cat fixture; this tests rendering states, not live photo delivery.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import os, base64, re
ROOT=Path(__file__).resolve().parents[1]
source=Path(os.environ.get('FREECAT_ATLAS_HTML', ROOT/'index.html')).read_text()
# A neutral one-pixel PNG used exclusively as a network-response fixture, never shipped as a cat photo.
PIXEL=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jf2sAAAAASUVORK5CYII=')
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None,args=['--no-sandbox'])
    for width,height in [(1440,900),(390,844),(320,720)]:
        page=browser.new_page(viewport={'width':width,'height':height},locale='zh-CN',is_mobile=width<600,has_touch=width<600,reduced_motion='reduce')
        requests=[];errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        def intercept(route):
            requests.append((route.request.url,route.request.headers.get('referer')))
            if 'Maine_Coon_Cat' in route.request.url: route.abort()
            else: route.fulfill(status=200,content_type='image/png',body=PIXEL)
        page.route(re.compile(r'https://(?:thumb|upload)\.wikimedia\.org/.*'),intercept)
        # set_content uses an opaque origin here; inject a per-page storage test double.
        fixture="<script>const fixtureStorage=new Map();Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>fixtureStorage.get(k)??null,setItem:(k,v)=>fixtureStorage.set(k,String(v)),removeItem:k=>fixtureStorage.delete(k)}});</script>"
        page.set_content(source.replace('<head>', '<head>'+fixture,1));page.wait_for_timeout(150)
        assert not requests,'Pet page must not request external photographs'
        page.locator('#worldNav [data-page=discover]').click()
        assert page.locator('#breedGrid article').count()==20
        assert page.locator('#breedGrid img[data-atlas-image]').count()==8
        assert page.locator('#breedGrid [data-photo-state=missing]').count()==12
        assert page.locator('#breedGrid svg').count()==0
        assert '8 有照片来源' in page.locator('#breedCount').inner_text()
        assert page.locator('#breedGrid img').evaluate_all("els=>els.every(e=>e.loading==='lazy'&&e.referrerPolicy==='no-referrer'&&!!e.alt)")
        assert page.locator('#breedGrid figcaption').count()==8
        assert page.locator('#breedGrid figcaption').evaluate_all("els=>els.every(e=>e.querySelector('a[href^=\"https://commons.wikimedia.org/wiki/File:\"]')&&e.querySelector('a[href^=\"https://creativecommons.org/licenses/\"]'))")
        page.locator('#breedSearch').fill('英国短毛猫')
        assert page.locator('#breedGrid article').count()==1
        page.locator('#breedGrid [data-photo-state=ready]').wait_for(timeout=10000)
        assert page.locator('#breedGrid img').evaluate('e=>e.naturalWidth>0')
        page.locator('#breedGrid [data-action=fav]').click()
        page.locator('#breedSearch').fill('缅因猫')
        page.locator('#breedGrid [data-photo-state=error]').wait_for(timeout=10000)
        assert '无法加载' in page.locator('#breedGrid [data-photo-state=error]').inner_text()
        assert page.locator('#breedGrid figcaption a').count()==2
        page.locator('#breedSearch').fill('波斯猫')
        assert '待补充' in page.locator('#breedGrid [data-photo-state=missing]').inner_text()
        page.locator('#breedSearch').fill('')
        page.locator('#worldNav [data-page=collection]').click()
        page.wait_for_timeout(100)
        before=len(requests)
        page.locator('#catForm [name=name]').fill('Test cat without photo')
        page.locator('#catForm [name=breed]').select_option('british')
        page.locator('#catForm button').click()
        page.get_by_text('未添加这只猫的真实照片',exact=True).wait_for()
        assert not page.locator('#hub img[data-atlas-image]').count()
        assert len(requests)==before,'Journal should not fetch reference photographs'
        page.locator('#worldNav [data-page=play]').click()
        assert not page.locator('#hub img[data-atlas-image]').count()
        page.locator('#worldNav [data-page=identify]').click()
        page.select_option('[name=coat]','long');page.select_option('[name=pattern]','point');page.locator('#matchForm button').click()
        assert '布偶' in page.locator('#matchResults').inner_text()
        page.locator('#worldNav [data-page=discover]').click();page.locator('#language').click()
        assert 'sourced photos' in page.locator('#breedCount').inner_text()
        assert page.locator('#breedGrid article').count()==20
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert all(not ref for _,ref in requests),requests
        assert not errors,errors
        print(f'PASS {width}x{height}: 20 entries, 8 sourced, 12 missing, loading/error, search, favorites, journal no-photo, identify, language; {len(requests)} intercepted requests',flush=True)
        page.close()
    browser.close()
