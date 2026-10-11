"""Headlines for IndexPilot (titles and links only, no article text). Run after update.py on every run.

Groups: central banks (Fed, ECB, Bank of Japan), markets (CNBC, MarketWatch), this week's index and
its top stock picks (Google News search feeds). Writes docs/data/news_feed.json.
A feed that fails is skipped; if every feed fails the previous file is kept.
"""
import datetime as dt, email.utils, json, os, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

D = sys.argv[1] if len(sys.argv) > 1 else 'docs/data'
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'}
log = lambda *a: print('[news]', *a, flush=True)
L = lambda n, d=None: json.load(open(os.path.join(D, n + '.json'))) if os.path.exists(os.path.join(D, n + '.json')) else d

QUERY = {'world': 'global stock markets', 'us': '"S&P 500"', 'ndx': '"Nasdaq 100" OR Nasdaq stocks', 'europe': 'European stocks STOXX',
         'japan': 'Nikkei Japan stocks', 'em': 'emerging markets stocks'}
gnews = lambda q: 'https://news.google.com/rss/search?' + urllib.parse.urlencode({'q': q + ' when:7d', 'hl': 'en-US', 'gl': 'US', 'ceid': 'US:en'})

now = (L('weekly_now') or [{}])[0]
pick = now.get('pick', 'world')
feeds = [
    ('Central banks', 'Federal Reserve', 'https://www.federalreserve.gov/feeds/press_all.xml', 6),
    ('Central banks', 'European Central Bank', 'https://www.ecb.europa.eu/rss/press.html', 6),
    ('Central banks', 'Bank of Japan', 'https://www.boj.or.jp/en/rss/whatsnew.xml', 4),
    ('Markets', 'CNBC', 'https://www.cnbc.com/id/100003114/device/rss/rss.html', 8),
    ('Markets', 'CNBC Economy', 'https://www.cnbc.com/id/20910258/device/rss/rss.html', 6),
    ('Markets', 'MarketWatch', 'https://feeds.content.dowjones.io/public/rss/mw_topstories', 8),
    ("This week's index", None, gnews(QUERY.get(pick, 'stock market')), 10),
]
for p in [p for p in (L('demo_positions') or []) if p.get('leg') == 'Stocks' and p.get('side') == 'Long'][:3]:
    name = re.sub(r'\b(Inc\.?|Corp\.?|Corporation|Co\.?,? Ltd\.?|Ltd\.?|Holdings?|Group|plc|AG|SA|N\.V\.|SE)\b', '', p['company']).strip(' ,.')
    feeds.append(('Stock picks', None, gnews(f'"{name}" stock'), 4))


def parse_date(s):
    if not s: return None
    try: return email.utils.parsedate_to_datetime(s).astimezone(dt.timezone.utc)
    except Exception: pass
    try: return dt.datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(dt.timezone.utc)
    except Exception: return None


rows, ok = [], 0
for group, source, url, n in feeds:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r: raw = r.read()
        root = ET.fromstring(raw)
        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
        got = 0
        for it in items:
            g = lambda tag: (it.findtext(tag) or it.findtext('{http://www.w3.org/2005/Atom}' + tag) or '').strip()
            title = re.sub(r'\s+', ' ', g('title'))
            link = g('link')
            if not link:
                a = it.find('{http://www.w3.org/2005/Atom}link'); link = a.get('href', '') if a is not None else ''
            src = source or (it.findtext('source') or '').strip() or 'Google News'
            if source is None and title.endswith(' - ' + src): title = title[: -len(src) - 3]
            when = parse_date(g('pubDate') or g('published') or g('updated') or it.findtext('{http://purl.org/dc/elements/1.1/}date'))
            if not title or not link: continue
            rows.append(dict(group=group, source=src, title=title[:220], link=link, published=when.strftime('%Y-%m-%dT%H:%M:%SZ') if when else None,
                             topic=now.get('pick_index') if group == "This week's index" else None))
            got += 1
            if got >= n: break
        ok += 1; log('ok', group, source or url[:60], got)
    except Exception as e:
        log('WARN', source or url[:80], e)
    time.sleep(0.5)

seen, out = set(), []
cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=21)
for r in sorted(rows, key=lambda r: r['published'] or '', reverse=True):
    k = re.sub(r'\W+', '', r['title'].lower())[:80]
    if k in seen: continue
    if r['published'] and dt.datetime.fromisoformat(r['published'].replace('Z', '+00:00')) < cutoff and r['group'] != 'Central banks': continue
    seen.add(k); out.append(r)
if ok == 0 or not out:
    log('no feeds worked; keeping the previous file'); sys.exit(0)
json.dump(out, open(os.path.join(D, 'news_feed.json'), 'w'), separators=(',', ':'))
meta = L('meta', {})
if 'news_feed' in meta:
    meta['news_feed']['updated'] = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'); json.dump(meta, open(os.path.join(D, 'meta.json'), 'w'), indent=1)
log('saved', len(out), 'headlines from', ok, 'feeds')
