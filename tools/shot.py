"""Screenshot helper (Playwright, phone size). Loads index.html with a fixture save, runs optional JS, saves a PNG.
Usage: python3 tools/shot.py out.png [fixture] [js]
  fixture: tools/fixtures/save_junior.json (default) or save_f1.json
  js: e.g. "()=>{title=false;tab='home';render()}"
"""
import sys,pathlib
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parent.parent
out=sys.argv[1];fx=sys.argv[2] if len(sys.argv)>2 else str(R/'tools/fixtures/save_junior.json');js=sys.argv[3] if len(sys.argv)>3 else "()=>{title=false;render()}"
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('file://'+str(R/'index.html'));pg.evaluate("s=>{localStorage.setItem('k2wc-save-v1',s)}",open(fx).read());pg.reload();pg.wait_for_timeout(500)
    pg.evaluate(js);pg.wait_for_timeout(500);pg.screenshot(path=out);print('errors:',errs);b.close()
