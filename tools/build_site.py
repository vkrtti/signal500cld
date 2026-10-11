"""Build docs/index.html (the public site) from page/body.html (the dashboard page body).

page/body.html is the single source: the same body runs inside the claude.ai dashboard
(as files/index.html) and inside the site wrapper (head with theme.css, d3, runtime.js; footer).
Run from the repo root: python3 tools/build_site.py
"""
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(ROOT, 'page/body.html')).read()
cur = open(os.path.join(ROOT, 'docs/index.html')).read()
head = cur[:cur.index('<div id="dash-root">') + len('<div id="dash-root">')]
tail = cur[cur.index('\n</div>\n\n<footer class="site-foot"'):]
old = '<span class="badge">Data to <b data-source="weekly_now" data-field="decided_on" data-row="0">—</b></span>'
assert old in src, 'badge anchor missing in page/body.html'
src = src.replace(old, old + '\n    <button class="themebtn" onclick="toggleTheme()" aria-label="Switch light/dark theme" title="Light / dark"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6"/></svg></button>')
tail = re.sub(r'<p>(Signal500|IndexPilot) is a personal research tool.*?</p>', "<p>IndexPilot is a personal research tool. Backtests, rankings and the demo account are simulations, not financial advice. Data: Yahoo Finance (ETF and stock prices), Federal Reserve Bank of St. Louis (FRED), Kenneth French data library, the public S&amp;P 500 company datasets on GitHub; headlines from the Federal Reserve, ECB, Bank of Japan, CNBC, MarketWatch and Google News.</p>", tail, count=1, flags=re.S)
if '<details><summary><b>Data sources' not in tail:
    tail = tail.replace('<b>Data sources and last update</b>\n  <table id="src-table"><tbody></tbody></table>', '<details><summary><b>Data sources and last update</b></summary>\n  <table id="src-table"><tbody></tbody></table></details>')
out = head + '\n' + src + tail
open(os.path.join(ROOT, 'docs/index.html'), 'w').write(out)
print('built docs/index.html', len(out), 'bytes')
