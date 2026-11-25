from pathlib import Path
import os
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
source = (root / 'index.html').read_text(encoding='utf-8')
anchor = 'updateLang();rebuild();requestAnimationFrame(frame);'
probe = '''window.__motion={angles:()=>limbs.map(l=>l.angle),pixels:()=>limbs.reduce((n,l)=>n+l.image.width*l.image.height,0),buffers:()=>limbs.map(l=>({actual:[l.image.width,l.image.height],expected:[l.box[2]*2,l.box[3]*2]})),screen(i,x,y){const l=limbs[i],c=Math.cos(l.angle),s=Math.sin(l.angle),dx=x-l.x,dy=y-l.y;const X=l.x+dx*c-dy*s,Y=l.y+dx*s+dy*c,r=canvas.getBoundingClientRect();return [r.x+tx+X*scale,r.y+ty+Y*scale*breath]},get active(){return petting},get eye(){return eyeOpen}};'''
assert source.count(anchor)==1
source=source.replace(anchor,probe+anchor)
with sync_playwright() as p:
    opts={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
    if os.getenv('CHROMIUM_PATH'): opts['executable_path']=os.environ['CHROMIUM_PATH']
    browser=p.chromium.launch(**opts)
    for w,h in [(1440,920),(390,844),(320,640)]:
        page=browser.new_page(viewport={'width':w,'height':h},locale='zh-CN',has_touch=w<500,is_mobile=w<500)
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(source);page.wait_for_timeout(500)
        a=page.evaluate('__motion.angles()');page.wait_for_timeout(600);b=page.evaluate('__motion.angles()')
        assert abs(a[0]-b[0])>0.0001,(a,b)
        # Ear-root geometry was expanded to prevent gaps. Check actual 2x
        # buffer sizing and retain a hard total allocation ceiling (250k px).
        buffers=page.evaluate('__motion.buffers()')
        assert len(buffers)==3 and all(b['actual']==b['expected'] for b in buffers),buffers
        pixels=page.evaluate('__motion.pixels()')
        assert 0<pixels<=250_000,pixels
        for i,x,y in [(0,482,333),(1,218,104),(2,400,104)]:
            page.wait_for_timeout(1400)
            X,Y=page.evaluate(f'__motion.screen({i},{x},{y})')
            if w<500: page.touchscreen.tap(X,Y)
            else: page.mouse.click(X,Y)
            page.wait_for_timeout(200)
            assert page.evaluate('__motion.active'),(w,i)
            angles=page.evaluate('__motion.angles()')
            assert all(abs(v)<.09 for v in angles),angles
        if os.getenv('FC_SCREENSHOTS'): page.screenshot(path=str(root/f'after-{w}.png'))
        for i in range(8):
            button=page.locator('#palette button').nth(i);button.click();assert button.get_attribute('aria-pressed')=='true'
        assert not errors, errors
        print(f'PASS {w}: moving tail/ears, transformed touch targets, 8 coats, no page errors')
        page.close()
    page=browser.new_page(viewport={'width':390,'height':844},reduced_motion='reduce')
    page.set_content(source);page.wait_for_timeout(500)
    assert page.evaluate('__motion.angles()')==[0,0,0]
    page.locator('#cat').focus();page.keyboard.press('Space');page.wait_for_timeout(150)
    assert page.evaluate('__motion.active && __motion.eye===0 && __motion.angles().every(a=>a===0)')
    print('PASS reduced motion and keyboard pet')
    browser.close()
