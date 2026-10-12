"""Screenshots of the built site: 1440px dark + light, 390px dark + light, every tab.

Usage (repo root): python3 tools/build_site.py && python3 tools/shots.py OUT_DIR [tab,tab,...]
Serves docs/ on a local port; d3 is served from tools/test/node_modules (run npm ci there first)
because the sandbox may not reach cdnjs. Prints JS errors and page width (must equal viewport width).
"""
import functools, http.server, os, sys, threading
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else 'shots'
TABS = (sys.argv[2] if len(sys.argv) > 2 else 'home,sim,longrun,strategy,stocks,extra,demo,indexes,week,news,markets,history,plans,gauges').split(',')
D3 = os.path.join(ROOT, 'tools/test/node_modules/d3/dist/d3.min.js')
os.makedirs(OUT, exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
H = functools.partial(Quiet, directory=os.environ.get('SITE_DIR', os.path.join(ROOT, 'docs')))  # SITE_DIR: test another copy of the site
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{srv.server_address[1]}/'
problems = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, w, h, theme in [('d', 1440, 900, 'dark'), ('l', 1440, 900, 'light'), ('p', 390, 844, 'dark'), ('pl', 390, 844, 'light')]:
        pg = b.new_page(viewport={'width': w, 'height': h})
        pg.on('pageerror', lambda e, n=name: problems.append(f'{n} JS error: {e}'))
        pg.route('https://cdnjs.cloudflare.com/**', lambda r: r.fulfill(path=D3, content_type='application/javascript'))
        pg.add_init_script(f"try{{localStorage.setItem('theme','{theme}')}}catch(e){{}}")
        pg.goto(url, wait_until='networkidle'); pg.wait_for_timeout(1200)
        for t in TABS:
            pg.evaluate(f"SX.show('{t}')"); pg.wait_for_timeout(400)
            sw = pg.evaluate('document.documentElement.scrollWidth')
            if sw > w: problems.append(f'{name} {t}: horizontal scroll ({sw}px > {w}px)')
            pg.screenshot(path=f'{OUT}/{name}_{t}.png', full_page=not name.startswith('p'))
    b.close()
print('\n'.join(problems) if problems else 'NO PROBLEMS', '| screenshots in', OUT)
sys.exit(1 if problems else 0)
