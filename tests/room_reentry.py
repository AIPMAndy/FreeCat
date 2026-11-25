from pathlib import Path
from playwright.sync_api import sync_playwright
import base64, json, os
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'room.html').read_text()
ASSETS=[('ginger',ROOT/'experiments/ginger.webp')]
if os.environ.get('FREECAT_PORTRAIT'): ASSETS.append(('portrait',Path(os.environ['FREECAT_PORTRAIT'])))
OUTPUT=os.environ.get('FREECAT_SCREENSHOTS')
if OUTPUT: Path(OUTPUT).mkdir(parents=True,exist_ok=True)

def html(source, asset):
 return source.replace("'experiments/ginger.webp'",repr('data:image/webp;base64,'+base64.b64encode(asset.read_bytes()).decode()))
def coords(page,p):
 return page.evaluate('p=>{const r=cv.getBoundingClientRect();return {x:r.left+r.width*(box[0]+p[0]*box[2]),y:r.top+r.height*(box[1]+p[1]*box[3])}}',p)
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None,args=['--no-sandbox'])
 for w,h in [(1440,900),(390,844),(320,720)]:
  for name,asset in ASSETS:
   p=b.new_page(viewport={'width':w,'height':h},locale='zh-CN',reduced_motion='reduce',has_touch=w<600,is_mobile=w<600,device_scale_factor=1)
   errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.set_content(html(SOURCE,asset));p.wait_for_function('!!mask && !cv.hidden && box[2]<1');p.wait_for_timeout(120)
   assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
   assert p.evaluate('hit(point)');assert p.locator('#status').inner_text()=='可以开始抚摸'
   if OUTPUT: p.screenshot(path=str(Path(OUTPUT)/f'{name}-{w}.png'))
   metrics=p.evaluate('()=>({width:box[2]*cv.clientWidth,height:box[3]*cv.clientHeight,stageHeight:cv.clientHeight,scrollHeight:document.documentElement.scrollHeight,alpha:mask.data.filter((v,i)=>i%4===3&&v>64).length/(mask.w*mask.h)})')
   center=coords(p,p.evaluate('point'));outside=coords(p,[.02,.02]);assert p.evaluate('!hit([.02,.02])')
   p.mouse.move(**center);p.mouse.down();p.wait_for_function('pressed');before=p.evaluate('cv.toDataURL()');p.mouse.move(center['x']+10,center['y']+8,steps=3);p.wait_for_timeout(120);assert p.evaluate('cv.toDataURL()')!=before
   p.mouse.move(**outside);p.wait_for_function('!pressed && activeId!==null');p.mouse.move(**center);p.wait_for_function('pressed && activeId!==null');p.mouse.up();p.wait_for_function('!pressed && activeId===null')
   p.locator('#cat').focus();p.keyboard.down('Space');p.wait_for_function('pressed');p.keyboard.up('Space');p.wait_for_function('!pressed')
   if w==390:
    session=p.context.new_cdp_session(p);session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[center]});p.wait_for_function('pressed');session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[outside]});p.wait_for_function('!pressed && activeId!==null');session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[center]});p.wait_for_function('pressed');session.send('Input.dispatchTouchEvent',{'type':'touchCancel','touchPoints':[]});p.wait_for_function('!pressed && activeId===null')
   p.locator('#sound').click();p.wait_for_function("audio && audio.state==='running' && soundButton.getAttribute('aria-pressed')==='true'");p.locator('#cat').focus();p.keyboard.down('Space');p.wait_for_function('purring && purrGain.gain.value>.005');p.keyboard.up('Space');p.wait_for_function('!purring');p.locator('#sound').click();assert p.evaluate('audio===null')
   p.locator('#night').click();assert p.evaluate("document.body.classList.contains('night')");p.locator('#language').click();assert p.locator('h1').inner_text()=='Stay a little.';assert len(p.locator('.nav a').all())==5;assert not errors,errors
   print(json.dumps(dict(w=w,asset=name,**metrics,errors=errors)),flush=True);p.close()
 # Transparent center keyboard fixture (one small opaque patch near top left)
 p=b.new_page(viewport={'width':390,'height':844},reduced_motion='reduce');p.set_content(html(SOURCE,ROOT/'experiments/ginger.webp'));p.wait_for_function('!!mask');p.evaluate('''()=>{const c=document.createElement('canvas');c.width=200;c.height=200;const x=c.getContext('2d');x.fillStyle='brown';x.fillRect(12,12,36,36);load(c.toDataURL())}''');p.wait_for_function('image.width===200 && !hit([.55,.5]) && hit(point)');p.locator('#cat').focus();p.keyboard.down('Space');p.wait_for_function('pressed');p.keyboard.up('Space');p.wait_for_function('!pressed');print('transparent-center keyboard passed',flush=True);p.close();b.close()
