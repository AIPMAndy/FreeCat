from playwright.sync_api import sync_playwright
from pathlib import Path
import hashlib, base64, os
root=Path(__file__).parent
with sync_playwright() as p:
 engine=os.environ.get('FREECAT_BROWSER','chromium')
 options={}
 if engine=='chromium':
  options['args']=['--no-sandbox']
  executable=os.environ.get('CHROMIUM_PATH') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else None)
  if executable: options['executable_path']=executable
 b=getattr(p,engine).launch(**options)
 for size in [(390,844),(1440,900)]:
  page=b.new_page(viewport=dict(width=size[0],height=size[1]),device_scale_factor=1,has_touch=size[0]<500)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content((root/'photo-touch.html').read_text().replace("img.src='sonkiki.webp'", "img.src='data:image/webp;base64,"+base64.b64encode((root/'sonkiki.webp').read_bytes()).decode()+"'"));page.wait_for_function('ready');page.screenshot(path=str(root/f'lab-{size[0]}-before.png'))
  result=page.evaluate('''() => { const snapshot=()=>ctx.getImageData(0,0,960,960).data;const before=snapshot();let ok=start([.57,.49],123);move([.60,.495]);vx=5;vy=3;force=1;base();paint();let after=snapshot(),inside=0,outside=0;for(let y=0;y<960;y++)for(let x=0;x<960;x++){let i=(y*960+x)*4;if(before[i]!==after[i]||before[i+1]!==after[i+1]||before[i+2]!==after[i+2]){if(((x/960-.57)/.15)**2+(((y+240)/1280-.49)/.06)**2<=1.03)inside++;else outside++}}end();return {ok,inside,outside,backgroundRejected:!hit(.5,.2),regions:regions.every(r=>hit(r[1],r[2])===r)}}''')
  assert result['ok'] and result['inside']>100 and result['outside']==0 and result['backgroundRejected'] and result['regions'],result
  box=page.locator('canvas').bounding_box();x=box['x']+box['width']*.57;y=box['y']+box['height']*((.49*1280-240)/960);page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+10,y+2,steps=4);page.wait_for_timeout(80);page.screenshot(path=str(root/f'lab-{size[0]}-touch.png'));page.mouse.up();page.wait_for_timeout(900);assert page.evaluate('raf===0 && active===null');page.locator('canvas').focus();page.keyboard.press('ArrowRight');page.keyboard.down('Space');assert page.evaluate('active==="key"');page.keyboard.up('Space');page.locator('#lang').click();assert page.locator('html').get_attribute('lang')=='zh-CN';assert not errors,errors
  
  if size[0]<500 and engine=='chromium':
   session=page.context.new_cdp_session(page);session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]});assert page.evaluate('active!==null');session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+8,'y':y+3}]});session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});assert page.evaluate('active===null');print('CDP mobile touch start/move/end OK')
  # One held pointer must survive the unpainted gap, without animating the sofa.
  def point(u,v):
   return box['x']+box['width']*u,box['y']+box['height']*((v*1280-240)/960)
  hx,hy=point(.28,.55);gx,gy=point(.5,.3)
  page.mouse.move(x,y);page.mouse.down();page.mouse.move(gx,gy)
  assert page.evaluate('active!==null && last===null')
  page.wait_for_timeout(900);assert page.evaluate('active!==null && raf===0')
  page.mouse.move(hx,hy);assert page.evaluate('active!==null && region[0]==="head" && last!==null')
  page.mouse.move(hx+6,hy);page.mouse.up();page.wait_for_timeout(900)
  assert page.evaluate('active===null && raf===0')
  assert not errors,errors
  print(engine,size,'held pointer gap/reentry/idle OK')
  page.emulate_media(reduced_motion='reduce');assert page.evaluate('motion.matches');assert page.evaluate('''() => {base();const before=ctx.getImageData(0,0,960,960).data;start([.57,.49],123);vx=5;force=1;paint();const after=ctx.getImageData(0,0,960,960).data;end();return before.every((v,i)=>v===after[i])}''');print(size,result,'mouse keyboard reduced motion idle OK');page.close()
 b.close()
