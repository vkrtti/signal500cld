"""Write the dashboard's files/index.html document from page/body.html.

The claude.ai dashboard caps one database document at 256 KiB, so the page is lightly minified first:
leading indentation is removed and blank lines dropped, except inside <pre>/<code>/<textarea> blocks and
inside JavaScript template literals that span several lines (tracked by backtick parity). Behaviour is unchanged;
run tools/test/page_test.js on the output to check.
Usage (repo root): python3 tools/dash_page.py OUT.json [--html OUT.html]
"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(ROOT, 'page/body.html')).read()
out, keep, in_script, in_tpl = [], 0, False, False
for line in src.split('\n'):
    low = line.lower()
    if not in_script and re.search(r'<script\b', low) and '</script>' not in low: in_script = True
    if keep or in_tpl: out.append(line)
    else:
        t = line.strip()
        if t: out.append(t)
    if in_script:
        code = re.sub(r"\\.", '', line)                      # ignore escaped characters
        code = re.sub(r"'[^']*'|\"[^\"]*\"", '', code) if not in_tpl else code
        code = re.sub(r'(?<!:)//.*$', '', code) if not in_tpl else code
        if code.count('`') % 2: in_tpl = not in_tpl
    if '</script>' in low: in_script = False; in_tpl = False
    keep += len(re.findall(r'<(pre|code|textarea)\b', low)) - len(re.findall(r'</(pre|code|textarea)>', low))
    keep = max(keep, 0)
text = '\n'.join(out)
doc = json.dumps({'text': text}, ensure_ascii=False)
open(sys.argv[1], 'w').write(doc)
if '--html' in sys.argv: open(sys.argv[sys.argv.index('--html') + 1], 'w').write(text)
n = len(doc.encode('utf-8')); print(f'dashboard page: {len(src)} -> {len(text)} chars, document {n} bytes (limit 262144)')
if n > 262000: sys.exit('too large for one dashboard document')
