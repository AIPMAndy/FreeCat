from pathlib import Path
import base64
from playwright.sync_api import sync_playwright
import json, os
ROOT=Path(__file__).resolve().parents[1]
OUT=os.environ.get('FREECAT_SCREENSHOTS')
if OUT: Path(OUT).mkdir(parents=True,exist_ok=True)
source=(ROOT/'room.html').read_text()
portrait='data:image/webp;base64,'+base64.b64encode((ROOT/'experiments/sleepy-tabby.webp').read_bytes()).decode()
icon='data:image/svg+xml;base64,'+base64.b64encode((ROOT/'assets/freecat.svg').read_bytes()).decode()
html=source.replace('experiments/sleepy-tabby.webp',portrait).replace('assets/freecat.svg',icon)
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None,args=['--no-sandbox'])
    for w,h in [(320,720),(390,844),(1440,900)]:
        page=browser.new_page(viewport={'width':w,'height':h},device_scale_factor=1,locale='zh-CN',has_touch=w<600,is_mobile=w<600,reduced_motion='no-preference')
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html)
        page.wait_for_function('!!mask && !cv.hidden && box[2]>0 && cv.width>1')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        metrics=page.evaluate('''()=>{
            const old=paintIdle;
            function frame(t,enabled){stop();paintIdle=enabled?old:()=>{};draw(t);if(raf)cancelAnimationFrame(raf);raf=0;return ctx.getImageData(0,0,cv.width,cv.height).data}
            function compare(t){const a=frame(t,false),b=frame(t,true);let changed=0,alpha=0,face=0,full=0;for(let y=0;y<cv.height;y++)for(let x=0;x<cv.width;x++){const i=(y*cv.width+x)*4;const d=Math.max(...[0,1,2,3].map(k=>Math.abs(a[i+k]-b[i+k])));if(d>3){changed++;if(Math.abs(a[i+3]-b[i+3])>3)alpha++;if(a[i+3]===255&&b[i+3]<248)full++;const u=(x/cv.width-box[0])/box[2],v=(y/cv.height-box[1])/box[3];if(u>.19&&u<.48&&v>.17&&v<.33)face++}}return {changed,alpha,face,full}}
            const quiet=compare(0),ear=compare(8205),tail=compare(8875);paintIdle=old;wake();return {quiet,ear,tail}
        }''')
        assert metrics['quiet']['changed']==0,metrics
        for key in ('ear','tail'):
            assert metrics[key]['changed']>20 and metrics[key]['alpha']>5 and metrics[key]['face']==0 and metrics[key]['full']==0,metrics
        # Freeze the same phase for baseline and candidate screenshots.
        if OUT:
            for enabled,name in [(False,'before'),(True,'after')]:
                page.evaluate('''enabled=>{stop();const saved=paintIdle;if(!enabled)paintIdle=()=>{};draw(8875);if(raf)cancelAnimationFrame(raf);raf=0;paintIdle=saved}''',enabled)
                page.screenshot(path=str(Path(OUT)/f'{name}-{w}.png'))
            page.evaluate('wake()')
        page.emulate_media(reduced_motion='reduce');page.wait_for_function('motion.matches')
        assert page.evaluate('''()=>{stop();draw(8205);const a=cv.toDataURL();draw(8875);const b=cv.toDataURL();return a===b}''')
        assert page.evaluate('''()=>{stop();draw(0);const before=cv.toDataURL();fit();return before===cv.toDataURL()}''')
        # Existing keyboard and pointer interactions still render after the animation.
        page.locator('#cat').focus();page.keyboard.down('Space');page.wait_for_function('pressed&&strength>.1');page.keyboard.up('Space');page.wait_for_function('!pressed');
        x,y=page.evaluate('''()=>{const r=cv.getBoundingClientRect();return [r.left+r.width*(box[0]+point[0]*box[2]),r.top+r.height*(box[1]+point[1]*box[3])]}''')
        page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+12,y+6,steps=4);page.wait_for_function('pressed&&strength>.1');page.mouse.up();page.wait_for_function('!pressed')
        if w==390:
            cdp=page.context.new_cdp_session(page);cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]});page.wait_for_function('pressed');cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_function('!pressed')
        page.locator('#sound').click();page.wait_for_function("audio&&audio.state==='running'");page.locator('#cat').focus();page.keyboard.down('Space');page.wait_for_function('purring&&purrGain.gain.value>.005');page.keyboard.up('Space');page.wait_for_function('!purring');page.locator('#sound').click()
        page.locator('#night').click();assert page.evaluate("document.body.classList.contains('night')");page.locator('#language').click();assert page.locator('h1').inner_text()=='Stay a little.'
        # Local photos never inherit the portrait's hand-mapped anatomy.
        page.emulate_media(reduced_motion='no-preference');page.evaluate("load(ROOM_CATS[0],false,null)");page.wait_for_function('selectedCat===null');assert page.evaluate('''()=>{stop();const w=cv.width,h=cv.height;ctx.clearRect(0,0,w,h);paintIdle(8205,0,0,w,h);return ctx.getImageData(0,0,w,h).data.every(x=>x===0)}''')
        assert not errors,errors
        print(json.dumps({'width':w,**metrics,'page_errors':errors},ensure_ascii=False),flush=True);page.close()
    browser.close()
