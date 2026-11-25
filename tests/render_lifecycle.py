from pathlib import Path
import os, sys
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
source=(Path(sys.argv[1]) if len(sys.argv)>1 else root/'index.html').read_text(encoding='utf-8')
anchor='updateLang();rebuild();requestAnimationFrame(frame);'
assert source.count(anchor)==1
source=source.replace('function frame(now){','function frame(now){window.__callbacks=(window.__callbacks||0)+1;',1)
source=source.replace(anchor,"window.__life={active:()=>petting,clock:()=>seconds,point:()=>[tx,ty,scale,breath],hit:(x,y)=>inside(x,y),eyes:()=>eyeOpen,angles:()=>limbs.map(l=>l.angle)};"+anchor)
with sync_playwright() as p:
    opts={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
    if os.getenv('CHROMIUM_PATH'): opts['executable_path']=os.environ['CHROMIUM_PATH']
    b=p.chromium.launch(**opts)
    for w,h in [(1440,920),(390,844),(320,640)]:
        page=b.new_page(viewport={'width':w,'height':h},locale='zh-CN',is_mobile=w<500,has_touch=w<500,device_scale_factor=1)
        page.set_default_timeout(8000)
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(source);page.wait_for_timeout(350)
        def count():
            a=page.evaluate('window.__callbacks||0');page.wait_for_timeout(700);return page.evaluate('window.__callbacks||0')-a
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        if os.getenv('FC_SCREENSHOTS'):page.screenshot(path=str(Path(os.environ['FC_SCREENSHOTS'])/f'after-{w}.png'))
        for x,y in [(310,150),(262,350),(360,470),(210,410),(425,405),(310,330)]: assert page.evaluate(f'__life.hit({x},{y})'),(x,y)
        for x,y in [(100,100),(100,450),(530,490)]: assert not page.evaluate(f'__life.hit({x},{y})'),(x,y)
        visible=count();assert visible>0
        page.locator('#cat').focus();page.keyboard.press('Space');page.wait_for_timeout(120);assert page.evaluate('__life.active()')
        page.locator('#worldNav [data-page=discover]').click();page.wait_for_timeout(250);hidden=count();assert hidden==0,(w,hidden)
        assert not page.evaluate('__life.active()')
        time0=page.evaluate('__life.clock()')
        page.locator('#worldNav [data-page=pet]').click();page.wait_for_timeout(350);resumed=count();assert resumed>0 and page.evaluate('__life.clock()')==time0,(w,resumed)
        page.evaluate('''()=>{let el=document.createElement('div');el.id='test-spacer';el.style.height='200vh';document.body.append(el);window.scrollTo({top:document.documentElement.scrollHeight,behavior:'instant'})}''')
        # The page has smooth scrolling; explicitly reach the target before
        # checking the offscreen render lifecycle rather than racing a timer.
        page.wait_for_function('document.querySelector("#stage").getBoundingClientRect().bottom<=0')
        page.wait_for_timeout(250)
        offscreen=count();assert offscreen==0,(w,offscreen)
        page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
        page.wait_for_function('document.querySelector("#stage").getBoundingClientRect().bottom>0 && document.querySelector("#stage").getBoundingClientRect().top<innerHeight')
        page.wait_for_timeout(350);back=count();assert back>0
        r=page.locator('#cat').bounding_box();tx,ty,scale,breath=page.evaluate('__life.point()');X,Y=r['x']+tx+310*scale,r['y']+ty+150*scale*breath
        if w<500:page.touchscreen.tap(X,Y)
        else:page.mouse.click(X,Y)
        page.wait_for_timeout(650);assert page.evaluate('__life.active() && __life.eyes()<.12'),(w,page.evaluate('__life.eyes()'))
        print(w,{'visible':visible,'other_tab':hidden,'resumed':resumed,'offscreen':offscreen,'returned':back},'PASS',flush=True)
        assert not errors,errors;page.close()
    page=b.new_page(viewport={'width':390,'height':844},reduced_motion='reduce');page.set_content(source);page.wait_for_timeout(350);assert page.evaluate('__life.eyes()===0 && __life.angles().every(a=>a===0)');page.locator('#cat').focus();page.keyboard.press('Space');page.wait_for_timeout(150);assert page.evaluate('__life.active() && __life.eyes()===0');print('reduced motion PASS',flush=True);b.close()
