"""Photo Lab: bounded directional displacement, recovery and silhouette regression."""
import base64
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
asset = Path(os.environ.get('FREECAT_PHOTO', ROOT / 'experiments/ginger.webp'))
source = (ROOT / 'experiments/photo-pet.html').read_text()
html = source.replace("load('ginger.webp')", "load('data:image/webp;base64," + base64.b64encode(asset.read_bytes()).decode() + "')")
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None, args=['--no-sandbox'])
    for width, height in [(1440, 900), (390, 844)]:
        page = browser.new_page(viewport={'width': width, 'height': height}, device_scale_factor=1, has_touch=width<600, is_mobile=width<600)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.set_content(html)
        canvas = page.locator('#cat')
        canvas.wait_for(state='visible')
        page.wait_for_timeout(200)
        rect = canvas.bounding_box()
        x,y = rect['x']+rect['width']*.55,rect['y']+rect['height']*.5
        page.mouse.move(x,y)
        page.mouse.down()
        page.mouse.move(x-rect['width']*.16,y-rect['height']*.05,steps=8)
        page.mouse.move(x+rect['width']*.16,y+rect['height']*.03,steps=12)
        page.mouse.up()
        page.wait_for_timeout(650)
        assert page.evaluate('!pressed && strength<.02 && trail.length>0 && trail.length<=TRAIL_LIMIT')
        # Compare at the same breathing phase with only the trail removed.
        result = page.evaluate('''()=>{const now=performance.now();cancelAnimationFrame(raf);raf=0;draw(now);cancelAnimationFrame(raf);raf=0;const a=ctx.getImageData(0,0,cv.width,cv.height).data;trail=[];draw(now);const b=ctx.getImageData(0,0,cv.width,cv.height).data;let changed=0,halo=0;for(let i=0;i<a.length;i+=4){if(Math.max(...[0,1,2].map(j=>Math.abs(a[i+j]-b[i+j])))>10)changed++;if(b[i+3]===0&&a[i+3]>8)halo++}return {changed,halo}}''')
        assert result['changed']>20, result
        assert result['halo']==0, result
        page.evaluate('''()=>{for(let i=0;i<20;i++)remember([(i%5)*.19+.05,Math.floor(i/5)*.22+.08],[.04,.02]);}''')
        assert page.evaluate('trail.length===TRAIL_LIMIT')
        page.wait_for_timeout(2400)
        assert page.evaluate('trail.length===0')
        page.evaluate('remember([.5,.5],[.04,.02]);reset()')
        assert page.evaluate('trail.length===0')
        page.emulate_media(reduced_motion='reduce')
        page.evaluate('remember([.5,.5],[.04,.02])')
        assert page.evaluate('trail.length===0')
        assert not errors, errors
        print(f'{width}px: residual changed pixels={result["changed"]}, silhouette halo={result["halo"]}; bounded, expires, reset, reduced motion passed')
        page.close()
    browser.close()
