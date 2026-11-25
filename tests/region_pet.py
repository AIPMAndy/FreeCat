"""Exercise exact bundled portrait, region profiles, scratch reuse and core room input.
Set FREECAT_SCREENSHOTS to save screenshots; optionally supply FREECAT_BASELINE for A/B.
The second bundled image is required unless FREECAT_ALLOW_PORTRAIT_SWITCH_FIXTURE=1.
In-memory HTML, not a network or physical-device test.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import os,base64,json
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'room.html').read_text()
portrait=ROOT/'experiments/sleepy-tabby.webp'
ginger=ROOT/'experiments/ginger.webp'
real_ginger=ginger.is_file()
assert real_ginger or os.environ.get('FREECAT_ALLOW_PORTRAIT_SWITCH_FIXTURE')=='1', 'Missing bundled ginger asset'
def uri(p,mime):return 'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()
def html(s):
    return s.replace('experiments/sleepy-tabby.webp',uri(portrait,'image/webp')).replace('experiments/ginger.webp',uri(ginger if real_ginger else portrait,'image/webp')).replace('experiments/chelsea.webp',uri(ROOT/'experiments/chelsea.webp','image/webp')).replace('assets/freecat.svg',uri(ROOT/'assets/freecat.svg','image/svg+xml'))
def pos(p,xy):return p.evaluate('xy=>{const r=cv.getBoundingClientRect();return {x:r.left+r.width*(box[0]+xy[0]*box[2]),y:r.top+r.height*(box[1]+xy[1]*box[3])}}',xy)
OUT=os.environ.get('FREECAT_SCREENSHOTS')
if OUT:Path(OUT).mkdir(parents=True,exist_ok=True)
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None,args=['--no-sandbox'])
    for w,h in [(1440,900),(390,844),(320,720)]:
        p=b.new_page(viewport={'width':w,'height':h},locale='zh-CN',reduced_motion='reduce',device_scale_factor=1,has_touch=w<600,is_mobile=w<600)
        errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
        p.route('https://**/*',lambda route:route.abort());p.set_content(html(source));p.wait_for_function('!!mask && selectedCat===PHOTO_CAT && !cv.hidden');p.locator('#nextCat').click();p.wait_for_function('selectedCat===0 && hit(point)');p.evaluate('soundMuted=true');p.wait_for_timeout(100)
        assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert p.locator('#status').inner_text()=='可以开始抚摸'
        if OUT:p.screenshot(path=str(Path(OUT)/f'after-{w}.png'))
        profiles=p.evaluate('''()=>PET_REGIONS.map((rs,i)=>rs.map(([x,y])=>petProfile([x,y],i)))''')
        for head,back,belly,tail in profiles:
            assert back['radius']>belly['radius']>head['radius']>tail['radius'],profiles
            assert back['gain']>belly['gain']>head['gain']>tail['gain'],profiles
        assert p.evaluate('petProfile([.31,.24],null).radius===1 && petProfile([.31,.24],null).gain===1')
        assert p.evaluate('PET_REGIONS[0].every(([x,y])=>hit([x,y]))')
        result=p.evaluate('''()=>{
          const points=PET_REGIONS[0].map(r=>r.slice(0,2)),w=cv.width,h=cv.height,x=box[0]*w,y=box[1]*h,iw=box[2]*w,ih=box[3]*h,r=Math.min(iw,ih)*.24;
          const baseline=()=>{ctx.clearRect(0,0,w,h);ctx.drawImage(image,x,y,iw,ih);return ctx.getImageData(0,0,w,h).data};
          const before=baseline(),count=[];
          for(const q of points){baseline();paintPatch(q,[.05,.025],1,x,y,iw,ih,r);const a=ctx.getImageData(0,0,w,h).data;let changed=0;for(let i=0;i<a.length;i+=4){if(Math.abs(a[i]-before[i])+Math.abs(a[i+1]-before[i+1])+Math.abs(a[i+2]-before[i+2])>8)changed++}count.push(changed)}
          baseline();paintPatch(points[1],[.05,.025],1,x,y,iw,ih,r*1.009);
          const initial=[patch.width,patch.height];let resizes=0,prev=initial.join();
          for(let j=0;j<20;j++)for(const q of points){baseline();paintPatch(q,[.05,.025],1,x,y,iw,ih,r*(1+.009*Math.sin(j/3)));const cur=[patch.width,patch.height].join();if(cur!==prev)resizes++;prev=cur}
          baseline();return {changed:count,scratch:initial,resizes};
        }''')
        assert all(n>50 for n in result['changed']),result
        assert result['changed'][1]>result['changed'][0]*1.25 and result['changed'][1]>result['changed'][3]*1.25,result
        assert result['resizes']==0,result
        xy=pos(p,[.76,.43]);outside=pos(p,[.01,.01]);assert not p.evaluate('hit([.01,.01])')
        before=p.evaluate('cv.toDataURL()');p.mouse.move(**xy);p.mouse.down();p.mouse.move(xy['x']-18,xy['y']+7,steps=5);p.wait_for_function('pressed && strength>.2');assert p.evaluate('cv.toDataURL()')!=before
        if OUT and w==390:p.screenshot(path=str(Path(OUT)/'after-active-390.png'))
        p.mouse.move(**outside);p.wait_for_function('!pressed && activeId!==null');p.mouse.move(**xy);p.wait_for_function('pressed && activeId!==null');p.mouse.up();p.wait_for_function('!pressed && activeId===null')
        p.locator('#cat').focus();p.keyboard.down('Space');p.wait_for_function('pressed');p.keyboard.up('Space');p.wait_for_function('!pressed')
        if w==390:
            cdp=p.context.new_cdp_session(p);cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[xy]});cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':xy['x']-8,'y':xy['y']+5}]});p.wait_for_function('pressed && strength>.2');cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});p.wait_for_function('!pressed')
        p.locator('#sound').click();p.wait_for_function("audio && audio.state==='running'");p.locator('#cat').focus();p.keyboard.down('Space');p.wait_for_function('purring');p.keyboard.up('Space');p.wait_for_function('!purring');p.locator('#sound').click()
        p.locator('#night').click();assert p.evaluate("document.body.classList.contains('night')")
        p.locator('#language').click();assert p.locator('h1').inner_text()=='Stay a little.'
        p.locator('#nextCat').click();p.wait_for_function('selectedCat===1');p.locator('#nextCat').click();p.wait_for_function('selectedCat===PHOTO_CAT');p.locator('#nextCat').click();p.wait_for_function('selectedCat===0')
        p.locator('#file').set_input_files(str(portrait));p.wait_for_function('selectedCat===null');assert p.evaluate('petProfile([.31,.24]).radius===1');assert not errors,errors
        print(json.dumps({'viewport':[w,h],'profiles':profiles,'render':result,'switch_exact_ginger':real_ginger,'errors':errors}))
        p.close()
        if os.environ.get('FREECAT_BASELINE'):
            p=b.new_page(viewport={'width':w,'height':h},locale='zh-CN',reduced_motion='reduce',device_scale_factor=1,has_touch=w<600,is_mobile=w<600)
            p.set_content(html(Path(os.environ['FREECAT_BASELINE']).read_text()));p.wait_for_function('!!mask && !cv.hidden && box[2]<1');
            if p.evaluate('selectedCat!==0'): p.locator('#nextCat').click();p.wait_for_function('selectedCat===0')
            p.wait_for_timeout(100)
            if OUT:p.screenshot(path=str(Path(OUT)/f'before-{w}.png'))
            r=p.evaluate('''()=>{const w=cv.width,h=cv.height,x=box[0]*w,y=box[1]*h,iw=box[2]*w,ih=box[3]*h,r=Math.min(iw,ih)*.24;paintPatch([.76,.43],[.05,.025],1,x,y,iw,ih,r*1.009);let prev=[patch.width,patch.height].join(),resizes=0;for(let j=0;j<20;j++)for(const q of [[.31,.24],[.76,.43],[.43,.61],[.38,.88]]){paintPatch(q,[.05,.025],1,x,y,iw,ih,r*(1+.009*Math.sin(j/3)));const cur=[patch.width,patch.height].join();if(cur!==prev)resizes++;prev=cur}return {resizes}}''')
            print(json.dumps({'baseline_viewport':[w,h],**r}));p.close()
    b.close()
