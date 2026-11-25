"""Real photograph, first-touch purr, interpolation and mute; in-memory Chromium.
This intentionally blocks the optional remote recording. Not a real-speaker/Pages test.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import base64, os
ROOT=Path(__file__).resolve().parents[1]
def uri(path,mime):return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()
html=(ROOT/'room.html').read_text()
for n in ('chelsea.webp','sleepy-tabby.webp','ginger.webp'):
    html=html.replace('experiments/'+n,uri(ROOT/'experiments'/n,'image/webp'))
html=html.replace('assets/freecat.svg',uri(ROOT/'assets/freecat.svg','image/svg+xml'))
html=html.replace('<head>','<head><script>window.fetch=()=>Promise.reject(Error("recording unavailable fixture"));</script>',1)
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None,args=['--no-sandbox','--disable-dev-shm-usage'])
    for w,h in [(1440,900),(390,844),(320,720)]:
        page=b.new_page(viewport={'width':w,'height':h},locale='zh-CN',device_scale_factor=1,has_touch=w<600,is_mobile=w<600,reduced_motion='no-preference')
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html);page.wait_for_function('!!mask&&selectedCat===PHOTO_CAT&&cv.width>1')
        page.wait_for_function('raf===0')
        assert page.evaluate('image.width===375&&image.height===300&&audio===null&&!purring')
        # Sample the exact bundled image. The core eye/nose regions must not move,
        # while cheek/forehead texture still responds to a bounded stroke.
        protected=page.evaluate('''()=>{
            const w=cv.width,h=cv.height,x=box[0]*w,y=box[1]*h,iw=box[2]*w,ih=box[3]*h,r=Math.min(iw,ih)*.24;
            const baseline=()=>{ctx.clearRect(0,0,w,h);ctx.drawImage(image,x,y,iw,ih);return ctx.getImageData(0,0,w,h).data};
            const a=baseline(),regions=[[.38,.385,.13,.15],[.78,.445,.11,.15],[.65,.81,.12,.11]],result=[];
            for(const p of [[.38,.385],[.78,.445],[.65,.81],[.19,.63],[.52,.15]]){
                baseline();paintPatch(p,[.042,.012],1,x,y,iw,ih,r);const b=ctx.getImageData(0,0,w,h).data;let changed=0,core=0;
                for(let j=0;j<h;j++)for(let i=0;i<w;i++){const k=(j*w+i)*4;if(Math.max(...[0,1,2,3].map(c=>Math.abs(a[k+c]-b[k+c])))<=2)continue;changed++;const u=(i+.5-x)/iw,v=(j+.5-y)/ih;if(regions.some(([cx,cy,sx,sy])=>Math.hypot((u-cx)/sx,(v-cy)/sy)<.60))core++}
                result.push({changed,core});
            }baseline();return result;
        }''')
        assert all(p['core']==0 for p in protected),protected
        assert all(p['changed']>50 for p in protected[-2:]),protected
        assert '真实摄影' in page.locator('#photoCredit').inner_text()
        assert page.locator('#photoSource').is_visible()
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        canvas=page.locator('#cat');canvas.scroll_into_view_if_needed();r=canvas.bounding_box()
        x,y=page.evaluate('()=>{const r=cv.getBoundingClientRect();return [r.left+(box[0]+.45*box[2])*r.width,r.top+(box[1]+.48*box[3])*r.height]}')
        before=page.evaluate('cv.toDataURL()');page.mouse.move(x,y);page.mouse.down()
        page.wait_for_function("audio&&audio.state==='running'&&purring&&purrGain.gain.value>.08")
        levels=page.evaluate('''()=>{const a=makePurrBuffer(audio).getChannelData(0);let sq=0,peak=0;for(let i=0;i<a.length;i++){sq+=a[i]*a[i];peak=Math.max(peak,Math.abs(a[i]))}return {rms:Math.sqrt(sq/a.length),peak}}''')
        assert .02<levels['rms']<.3 and levels['peak']<.8,levels
        page.mouse.move(x+min(60,r['width']*.15),y+12,steps=1);page.wait_for_timeout(100)
        assert page.evaluate('Math.hypot(...target)<=.042001&&trail.length<=8&&trail.length>=2')
        assert before!=page.evaluate('cv.toDataURL()')
        page.mouse.up();page.wait_for_function('!purring&&purrGain.gain.value<.02',timeout=4000)
        page.wait_for_function('raf===0&&trail.length===0',timeout=4000)
        still=page.evaluate('cv.toDataURL()');page.wait_for_timeout(250);assert page.evaluate('raf===0') and still==page.evaluate('cv.toDataURL()')
        page.locator('#sound').click();assert page.evaluate('audio===null&&soundMuted')
        page.mouse.move(x,y);page.mouse.down();page.mouse.up();page.wait_for_timeout(180)
        assert page.evaluate('audio===null')
        page.locator('#sound').click();page.wait_for_function('audio&&purring&&purrGain.gain.value>.05')
        page.wait_for_function('!purring&&purrGain.gain.value<.02',timeout=4000)
        page.locator('#nextCat').click();page.wait_for_function('selectedCat===0');assert 'AI' in page.locator('#photoCredit').inner_text()
        page.locator('#nextCat').click();page.wait_for_function('selectedCat===1')
        page.locator('#nextCat').click();page.wait_for_function('selectedCat===PHOTO_CAT')
        assert '真实摄影' in page.locator('#photoCredit').inner_text()
        page.locator('#language').click();assert 'Real photograph' in page.locator('#photoCredit').inner_text()
        assert not errors,errors
        print(f'{w}: photo, sound fallback, stroke, mute, switch, translation, layout; {levels}; face protection {protected}',flush=True);page.close()
    b.close()
