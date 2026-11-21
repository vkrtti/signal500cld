"""Next results (earnings) dates for every stock the site currently holds or trades. Run after update.py on every run.

Stocks: the demo account's stocks, Free Money Keepers (A/B) and the weekly long/short (extra_positions).
Source: Yahoo Finance via yfinance (keyless): Ticker.calendar, then Ticker.get_earnings_dates as a fallback.
Dates are the company's announced or Yahoo's estimated date; they can move. Writes docs/data/earnings_next.json.
A ticker that fails keeps its previous row (if that date is still ahead); if every lookup fails the file is kept.
"""
import datetime as dt, json, os, sys, time

D = sys.argv[1] if len(sys.argv) > 1 else 'docs/data'
log = lambda *a: print('[earnings]', *a, flush=True)
L = lambda n, d=None: json.load(open(os.path.join(D, n + '.json'))) if os.path.exists(os.path.join(D, n + '.json')) else d
TODAY = dt.datetime.now(dt.timezone.utc).date()

where = {}   # ticker -> {'company':..., 'where': [...]}
def add(t, company, label):
    if not t: return
    w =where.setdefault(t, {'company': company or t, 'where': []})
    if label not in w['where']: w['where'].append(label)
for p in L('demo_positions', []) or []:
    if p.get('leg') == 'Stocks': add(p.get('ticker'), p.get('company'), 'Demo')
for p in L('free_money_holdings', []) or []:
    add(p.get('ticker'), p.get('company'), 'Keepers ' + str(p.get('strategy', '')))
for p in L('extra_positions', []) or []:
    add(p.get('ticker'), p.get('company'), 'Long/short ' + str(p.get('side', '')).lower())

prev = {r['ticker']: r for r in (L('earnings_next', []) or [])}


def to_date(x):
    try:
        if hasattr(x, 'date'): x = x.date()
        if isinstance(x, dt.date): return x
        return dt.date.fromisoformat(str(x)[:10])
    except Exception:
        return None


def lookup(t):
    import yfinance as yf
    tk = yf.Ticker(t)
    dates = []
    try:
        cal = tk.calendar
        if isinstance(cal, dict): dates = [to_date(x) for x in (cal.get('Earnings Date') or [])]
        elif cal is not None and hasattr(cal, 'loc') and 'Earnings Date' in getattr(cal, 'index', []):
            dates = [to_date(x) for x in cal.loc['Earnings Date'].tolist()]
    except Exception as e:
        log(t, 'calendar failed:', type(e).__name__)
    dates = sorted(d for d in dates if d and d >= TODAY)
    if not dates:
        try:
            ed = tk.get_earnings_dates(limit=8)
            if ed is not None and len(ed): dates = sorted(d for d in (to_date(x) for x in ed.index) if d and d >= TODAY)
        except Exception as e:
            log(t, 'earnings_dates failed:', type(e).__name__)
    return dates[0] if dates else None


rows, ok = [], 0
for t, info in where.items():
    d = None
    for attempt in range(2):
        try:
            d = lookup(t); break
        except Exception as e:
            log(t, 'error', type(e).__name__); time.sleep(3)
    if d: ok += 1
    elif t in prev and prev[t].get('next_date') and to_date(prev[t]['next_date']) and to_date(prev[t]['next_date']) >= TODAY:
        d = to_date(prev[t]['next_date']); log(t, 'kept previous date', d)
    rows.append({'ticker': t, 'company': info['company'], 'where': info['where'],
                 'next_date': d.isoformat() if d else None,
                 'days': (d - TODAY).days if d else None,
                 'within_week': bool(d and (d - TODAY).days <= 7)})
    time.sleep(0.5)

if where and ok == 0 and prev:
    log('every lookup failed; previous file kept'); sys.exit(0)
rows.sort(key=lambda r: (r['next_date'] is None, r['next_date'] or '', r['ticker']))
json.dump(rows, open(os.path.join(D, 'earnings_next.json'), 'w'), separators=(',', ':'))
meta = L('meta', {})
if 'earnings_next' in meta:
    meta['earnings_next']['updated'] = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    json.dump(meta, open(os.path.join(D, 'meta.json'), 'w'), indent=1)
log(f'{ok}/{len(where)} dates found; saved earnings_next ({len(rows)} rows)')
