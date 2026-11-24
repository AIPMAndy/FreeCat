from pathlib import Path
import os, sys, statistics
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
source = Path(sys.argv[1]).read_text(encoding='utf-8') if len(sys.argv)>1 else (root/'index.html').read_text(encoding='utf-8')
# Test-only hook: inspect actual paths and cached bitmaps in the real renderer.
anchor='updateLang();rebuild();requestAnimationFrame(frame);'
assert source.count(anchor)==1
hook='''
window.__faceTest={
  gaps(){const mask=document.createElement('canvas');mask.width=620;mask.height=570;const g=mask.getContext('2d');let results=[];
    for(const l of limbs.slice(1))for(const a of [-.08,-.04,0,.04,.08]){
      g.clearRect(0,0,620,570);g.fillStyle='#000';g.save();g.translate(l.x,l.y);g.rotate(a);g.translate(-l.x,-l.y);g.fill(l.p);g.restore();g.fill(head);
      // Interior ear-root bridge: these points must never reveal the backdrop.
      const pts=l===limbs[1]?[[227,139],[233,135],[239,131],[245,126],[251,122]]:[[390,139],[384,135],[378,131],[372,126],[366,122]];
      results.push({angle:a,ear:l===limbs[1]?'L':'R',missing:pts.filter(([x,y])=>g.getImageData(x,y,1,1).data[3]<230).length});
    }return results;},
  benchmark(){const samples=[];for(let k=0;k<8;k++){coat=k;let a=performance.now();rebuild();samples.push(performance.now()-a)}coat=0;rebuild();return samples;},
  state(){return {eye:eyeOpen,limbs:limbs.map(l=>l.angle),petting}},
  cache(){return limbs.slice(1).map(l=>({w:l.image.width,h:l.image.height}))}
};
'''
source=source.replace(anchor,anchor+hook)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox','--disable-dev-shm-usage'])
    for w,h in [(1440,920),(390,844)]:
        page=browser.new_page(viewport={'width':w,'height':h},locale='zh-CN',is_mobile=w<500,has_touch=w<500)
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(source);page.wait_for_timeout(400)
        gaps=page.evaluate('__faceTest.gaps()');missing=sum(x['missing'] for x in gaps)
        print(f'{w}x{h}: missing ear-root samples {missing}/50; {gaps}',flush=True)
        if len(sys.argv)==1: assert missing==0,gaps
        label='before' if len(sys.argv)>1 else 'after'
        page.screenshot(path=str(root/f'{label}-{w}.png'))
        page.locator('#cat').focus();page.keyboard.press('Space');page.wait_for_timeout(300)
        assert page.evaluate('__faceTest.state().petting')
        if w==1440:
            samples=page.evaluate('__faceTest.benchmark()');print('8 coat rebuilds ms:',samples,'median',statistics.median(samples),flush=True)
        assert not errors,errors
        page.close()
    browser.close()
