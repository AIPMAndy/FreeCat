"""In-memory Chromium regression: default image, anatomy-local idle motion and upload bounds.
No device or public-deployment claims. Run with playwright/Chromium installed.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import base64, json, os
ROOT=Path(__file__).resolve().parents[1]
OUT=os.environ.get('FREECAT_SCREENSHOTS')
if OUT: Path(OUT).mkdir(parents=True,exist_ok=True)
def uri(path,mime):return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()
def html(path):
    return path.read_text().replace('experiments/sleepy-tabby.webp',uri(ROOT/'experiments/sleepy-tabby.webp','image/webp')).replace('experiments/chelsea.webp',uri(ROOT/'experiments/chelsea.webp','image/webp')).replace('assets/freecat.svg',uri(ROOT/'assets/freecat.svg','image/svg+xml'))
# Direct deterministic frame sampling, not a device FPS benchmark.
SAMPLE='''()=>{const w=cv.width,h=cv.height;stop();const frame=t=>{draw(t);const a=ctx.getImageData(0,0,w,h).data;stop();return a};const a=frame(0),b=frame(680*Math.PI/2);let face=0,torso=0,total=0;for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=(y*w+x)*4;if(Math.abs(a[i]-b[i])+Math.abs(a[i+1]-b[i+1])+Math.abs(a[i+2]-b[i+2])<=8)continue;total++;const u=(x/w-box[0])/box[2],v=(y/h-box[1])/box[3];if(u>.15&&u<.45&&v>.12&&v<.36)face++;if(u>.48&&u<.86&&v>.36&&v<.73)torso++}wake();return {face,torso,total}}'''
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None,args=['--no-sandbox'])
    for w,h in [(1440,900),(390,844),(320,720)]:
        static=b.new_page(viewport={'width':w,'height':h},java_script_enabled=False,has_touch=w<600,is_mobile=w<600,device_scale_factor=1)
        static.set_content(html(ROOT/'room.html'))
        assert static.locator('#preview').is_visible() and static.locator('#cat').is_hidden()
        # Playwright evaluate can inspect the DOM even with document JS disabled.
        assert static.locator('#preview').evaluate('el=>el.complete&&el.naturalWidth===375&&el.naturalHeight===300')
        assert static.locator('noscript').inner_text().strip()
        if OUT: static.screenshot(path=str(Path(OUT)/f'firstpaint-{w}.png'))
        static.close()
        p=b.new_page(viewport={'width':w,'height':h},locale='zh-CN',has_touch=w<600,is_mobile=w<600,device_scale_factor=1,reduced_motion='no-preference')
        errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
        p.route('https://**/*',lambda route:route.abort());p.set_content(html(ROOT/'room.html'));p.wait_for_function('!!mask && selectedCat===PHOTO_CAT && !cv.hidden && hit(point)');assert p.locator('#preview').is_hidden();assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
        p.locator('#nextCat').click();p.wait_for_function('selectedCat===0 && hit(point)');p.evaluate('soundMuted=true')
        r=p.evaluate(SAMPLE);assert r['face']==0 and r['torso']>50,r
        p.emulate_media(reduced_motion='reduce');p.wait_for_timeout(100);still=p.evaluate(SAMPLE);assert still['total']==0,still
        if OUT:p.screenshot(path=str(Path(OUT)/f'after-{w}.png'))
        assert p.evaluate('mask.w<=384 && mask.h<=384')
        # A fully transparent upload must not replace a valid cat.
        p.evaluate('''()=>{window.oldImage=image;const c=document.createElement('canvas');c.width=64;c.height=64;load(c.toDataURL())}''')
        p.wait_for_function("status.dataset.raw.includes('previous cat kept')");assert p.evaluate('image===window.oldImage && selectedCat===0 && hit(point)')
        # A 1×1600 source previously requested a 409600px mask canvas.
        p.evaluate('''()=>{const c=document.createElement('canvas');c.width=1;c.height=1600;const cc=c.getContext('2d');cc.fillStyle='#a76b42';cc.fillRect(0,0,1,1600);load(c.toDataURL())}''')
        p.wait_for_function('selectedCat===null && image.width===1');assert p.evaluate('mask.w===1 && mask.h===384 && hit(point)')
        p.locator('#cat').focus();p.keyboard.down('Space');p.wait_for_function('pressed');p.keyboard.up('Space');p.wait_for_function('!pressed')
        # A tiny isolated opaque pixel at an odd coordinate is keyboard-reachable.
        p.evaluate('''()=>{const c=document.createElement('canvas');c.width=64;c.height=64;const cc=c.getContext('2d');cc.fillStyle='brown';cc.fillRect(11,13,1,1);load(c.toDataURL())}''')
        p.wait_for_function('image.width===64 && mask.w===64 && hit(point)');p.locator('#cat').focus();p.keyboard.down('Space');p.wait_for_function('pressed');p.keyboard.up('Space');p.wait_for_function('!pressed')
        p.locator('summary').click();p.locator('#defaultCat').click();p.wait_for_function('selectedCat===PHOTO_CAT && hit(point)');assert not errors,errors
        print(json.dumps({'viewport':[w,h],'motion':r,'reduced_motion':still,'first_paint':'exact bundled WebP inlined, JavaScript disabled','mask':[p.evaluate('mask.w'),p.evaluate('mask.h')],'errors':errors}),flush=True);p.close()
        baseline=os.environ.get('FREECAT_BASELINE')
        if baseline:
            q=b.new_page(viewport={'width':w,'height':h},locale='zh-CN',has_touch=w<600,is_mobile=w<600,device_scale_factor=1,reduced_motion='no-preference')
            q.set_content(html(Path(baseline)));q.wait_for_function('!!mask && !cv.hidden && hit(point)');
            if q.evaluate('selectedCat!==0'): q.locator('#nextCat').click();q.wait_for_function('selectedCat===0 && hit(point)')
            print(json.dumps({'baseline':[w,h],'motion':q.evaluate(SAMPLE)}),flush=True);q.close()
    b.close()
