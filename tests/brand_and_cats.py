"""FreeCat room: bundled resource paths, accessible brand and two bundled cats."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import mimetypes, os, json, base64
ROOT=Path(__file__).resolve().parents[1]
OUT=os.environ.get('FREECAT_SCREENSHOTS')
SOURCE=(ROOT/'room.html').read_text()
def uri(path):
    f=ROOT/path
    return 'data:'+mimetypes.guess_type(f.name)[0]+';base64,'+base64.b64encode(f.read_bytes()).decode()
for path in ('assets/freecat.svg','assets/favicon-32.png','assets/apple-touch-icon.png','assets/social-card.jpg','experiments/sleepy-tabby.webp','experiments/ginger.webp'):
    assert (ROOT/path).is_file(), path
HTML=SOURCE.replace('src="assets/freecat.svg"','src="'+uri('assets/freecat.svg')+'"')
for path in ('experiments/sleepy-tabby.webp','experiments/ginger.webp'):
    HTML=HTML.replace(path,uri(path))
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or '/usr/bin/chromium',args=['--no-sandbox'])
    for w,h in [(1440,900),(390,844),(320,720)]:
        page=b.new_page(viewport={'width':w,'height':h},locale='zh-CN',device_scale_factor=1,reduced_motion='reduce',has_touch=w<600,is_mobile=w<600)
        errors=[];missing=[];requests=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('response',lambda r:missing.append(r.url) if r.status>=400 else None)
        page.on('request',lambda r:requests.append(r.url))
        page.set_content(HTML)
        page.wait_for_function('!!mask && selectedCat===0 && image.height>image.width')
        page.wait_for_function('document.querySelector(".brand-icon").naturalWidth>0')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert page.locator('#nextCat').inner_text()=='换只猫'
        assert page.locator('link[rel="apple-touch-icon"]').get_attribute('href')=='assets/apple-touch-icon.png'
        assert page.evaluate('loadId===1'), 'one image load before explicit switch'
        if OUT:page.screenshot(path=str(Path(OUT)/f'portrait-{w}.png'))
        canvas=page.locator('#cat');r=canvas.bounding_box();x=r['x']+r['width']*(page.evaluate('box[0]+box[2]*.55'));y=r['y']+r['height']*.5
        assert page.evaluate('hit([.55,.5])')
        before=page.evaluate('cv.toDataURL()');page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+12,y+4,steps=3);page.wait_for_timeout(120);assert page.evaluate('pressed && strength>.2');assert before!=page.evaluate('cv.toDataURL()');page.mouse.up()
        canvas.focus();page.keyboard.down('Space');page.wait_for_function('pressed');page.keyboard.up('Space');page.wait_for_function('!pressed')
        page.locator('#nextCat').click();page.wait_for_function('selectedCat===1 && image.width>image.height && !cv.parentElement.classList.contains("portrait")');assert page.evaluate('!pressed && trail.length===0')
        if OUT:page.screenshot(path=str(Path(OUT)/f'ginger-{w}.png'))
        # Both built-in cats must be interactive, including stroke re-entry.
        center=page.evaluate('()=>{const r=cv.getBoundingClientRect();return {x:r.left+r.width*(box[0]+point[0]*box[2]),y:r.top+r.height*(box[1]+point[1]*box[3])}}')
        outside=page.evaluate('()=>{const r=cv.getBoundingClientRect();return {x:r.left+r.width*(box[0]+.01*box[2]),y:r.top+r.height*(box[1]+.01*box[3])}}')
        assert page.evaluate('hit(point) && !hit([.01,.01])')
        page.mouse.move(**center);page.mouse.down();page.wait_for_function('pressed');page.mouse.move(**outside);page.wait_for_function('!pressed && activeId!==null');page.mouse.move(**center);page.wait_for_function('pressed && activeId!==null');page.mouse.up();page.wait_for_function('!pressed && activeId===null')
        page.locator('#nextCat').click();page.wait_for_function('selectedCat===0 && image.height>image.width')
        page.locator('#sound').click();page.wait_for_function('audio && audio.state==="running"');canvas.focus();page.keyboard.down('Space');page.wait_for_function('purring && purrGain.gain.value>.005');page.keyboard.up('Space');page.wait_for_function('!purring');page.locator('#sound').click();assert page.evaluate('audio===null')
        if w==390:
            r=canvas.bounding_box();x=r['x']+r['width']*page.evaluate('box[0]+box[2]*.55');y=r['y']+r['height']*.5
            cdp=page.context.new_cdp_session(page);cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]});cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+12,'y':y+4}]});page.wait_for_function('pressed && strength>.2');cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_function('!pressed')
        page.locator('#night').click();assert page.locator('meta[name="theme-color"]').get_attribute('content')=='#252c28'
        if OUT:page.screenshot(path=str(Path(OUT)/f'night-{w}.png'))
        page.locator('#language').click();assert page.locator('#nextCat').inner_text()=='Another cat';assert page.locator('h1').inner_text()=='Stay a little.'
        # local photo remains an option, resets selectedCat to null, next restores portrait.
        page.locator('#file').set_input_files(str(ROOT/'experiments/ginger.webp'));page.wait_for_function('selectedCat===null && image.width>image.height');page.locator('#nextCat').click();page.wait_for_function('selectedCat===0 && image.height>image.width')
        assert page.locator('.nav a').evaluate_all('els=>els.map(e=>e.getAttribute("href"))')==['index.html#discover','index.html#identify','index.html#collection','index.html#care','index.html#play']
        assert not errors,errors;assert not missing,missing
        print(json.dumps({'width':w,'catWidth':page.evaluate('box[2]*cv.clientWidth'),'catHeight':page.evaluate('box[3]*cv.clientHeight'),'errors':errors,'failedRequests':missing,'imageLoads':page.evaluate('loadId')},ensure_ascii=False),flush=True)
        page.close()
    b.close()
