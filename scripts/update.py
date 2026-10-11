"""IndexPilot data update. Run by GitHub Actions (see .github/workflows/update.yml).

Daily (every run): refreshes market indicators, the monthly US signal, the markets table
from the Federal Reserve (FRED) and the public S&P 500 datasets.
Weekly (--weekly, the Saturday run): also picks the main index, sets next week's buy amount and the
signal meter, ranks the picked index's stocks and rolls the demo account (via indexpilot.py).

Usage: python scripts/update.py [--weekly] [--data docs/data] [--offline DIR]
--offline DIR reads <SERIES>.csv / fin.csv / cons.csv from DIR instead of the internet (for testing).
A source that fails keeps its previous data; the run never deletes data.
"""
import argparse, datetime as dt, io, json, os, subprocess, sys, time, urllib.request
import numpy as np, pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('--weekly', action='store_true')
ap.add_argument('--data', default='docs/data')
ap.add_argument('--offline')
ap.add_argument('--research', default='research_data')
args = ap.parse_args()
D = args.data
NOW = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
UA = {'User-Agent': 'Mozilla/5.0 (IndexPilot data updater; +https://github.com)'}
log = lambda *a: print('[update]', *a, flush=True)

def load(name, default=None):
    p = os.path.join(D, name + '.json')
    return json.load(open(p)) if os.path.exists(p) else default

def save(name, obj):
    json.dump(obj, open(os.path.join(D, name + '.json'), 'w'), separators=(',', ':'))
    meta = load('meta', {})
    if name in meta: meta[name]['updated'] = NOW
    json.dump(meta, open(os.path.join(D, 'meta.json'), 'w'), indent=1)
    log('saved', name)

def get_text(url, offline_name):
    if args.offline:
        return open(os.path.join(args.offline, offline_name)).read()
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read().decode('utf-8')
        except Exception as e:
            log(f'fetch failed ({attempt + 1}/4) {url}: {e}'); time.sleep(5 * (attempt + 1))
    raise RuntimeError('could not fetch ' + url)

LONG = {'VIXCLS': '2010-01-01', 'NFCI': '2010-01-01', 'SAHMREALTIME': '2010-01-01', 'T10Y3M': '2010-01-01', 'NASDAQCOM': '1971-01-01', 'NASDAQ100': '1986-01-01', 'NIKKEI225': '1960-01-01', 'DEXUSEU': '1999-01-01', 'CBBTCUSD': '2014-12-01', 'DCOILBRENTEU': '1987-01-01'}

def fred(series, start=None):
    start = start or LONG.get(series, '2015-01-01')
    txt = get_text(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}&cosd={start}', series + '.csv')
    df = pd.read_csv(io.StringIO(txt))
    df.columns = ['date', 'v']
    df['v'] = pd.to_numeric(df.v, errors='coerce')
    df = df.dropna()
    df['date'] = pd.to_datetime(df.date)
    if df.empty: raise RuntimeError('no rows for ' + series)
    return df.set_index('date').v

# ---------------------------------------------------------------- fetch
S = {}
for sid in ['SP500', 'VIXCLS', 'NFCI', 'SAHMREALTIME', 'T10Y3M', 'BAMLH0A0HYM2', 'DFF', 'DGS10', 'UNRATE', 'CPIAUCSL',
            'NASDAQCOM', 'NASDAQ100', 'DJIA', 'NIKKEI225', 'DEXUSEU', 'DCOILBRENTEU', 'DTWEXBGS', 'CBBTCUSD']:
    try: S[sid] = fred(sid); log(sid, 'ok', S[sid].index[-1].date(), S[sid].iloc[-1])
    except Exception as e: log('WARN', sid, e)
GH = 'https://raw.githubusercontent.com/datasets/'
os.makedirs('work', exist_ok=True)
fund_ok = True
try:
    open('work/fin.csv', 'w').write(get_text(GH + 's-and-p-500-companies-financials/main/data/constituents-financials.csv', 'fin.csv'))
    open('work/cons.csv', 'w').write(get_text(GH + 's-and-p-500-companies/main/data/constituents.csv', 'cons.csv'))
except Exception as e:
    fund_ok = False; log('WARN fundamentals', e)

last = lambda s: (float(s.iloc[-1]), s.index[-1].strftime('%Y-%m-%d'))

# ---------------------------------------------------------------- daily: S&P weekly chart, indicators, monthly signal
if 'SP500' in S:
    sp = S['SP500']
    spx, spx_date = last(sp)
    ma200 = float(sp.iloc[-200:].mean()); ma50 = float(sp.iloc[-50:].mean())
    ath = max(float(sp.max()), float((load('weekly_now') or [{}])[0].get('ath', 0)))
    yr = sp[sp.index >= sp.index[-1] - pd.Timedelta(days=365)]
    wk = sp.groupby(sp.index.to_period('W')).tail(1)
    wk = wk[wk.index >= sp.index[-1] - pd.Timedelta(days=730)]
    save('spx_weekly', [dict(date=d.strftime('%Y-%m-%d'), close=int(round(v))) for d, v in wk.items()])

    ind = load('indicators', [])
    byk = {r['key']: r for r in ind}
    def setk(key, value, display, status=None, asof=None, meaning=None):
        if key not in byk: return
        r = byk[key]; r['value'] = value; r['display'] = display
        if status: r['status'] = status
        if asof: r['asof'] = asof
        if meaning: r['meaning'] = meaning
    above = spx / ma200 - 1; dd = spx / ath - 1
    setk('spx', round(spx, 2), f'{spx:,.0f}', asof=spx_date)
    setk('above200', round(above * 100, 2), f'{above * 100:+.1f}%', 'good' if above > 0 else 'bad', spx_date)
    setk('drawdown', round(dd * 100, 2), f'{dd * 100:.1f}%', 'good' if dd <= -0.15 else 'neutral', spx_date,
         'No discount on offer: the index is at or near its record.' if dd > -0.05 else f'The index is {abs(dd) * 100:.0f}% below its record.')
    if 'VIXCLS' in S:
        v, d = last(S['VIXCLS']); setk('vix', v, f'{v:.1f}', 'good' if v >= 30 else 'warn' if v >= 20 else 'neutral', d,
                                      'Panic: historically a good entry.' if v >= 30 else 'Nervous.' if v >= 20 else 'Calm. No panic discount.')
    if 'T10Y3M' in S:
        v, d = last(S['T10Y3M']); setk('curve', v, f'{v:+.2f} pp', 'good' if v >= 0 else 'bad', d)
    if 'SAHMREALTIME' in S:
        v, d = last(S['SAHMREALTIME']); setk('sahm', v, f'{v:.2f}', 'bad' if v >= 0.5 else 'warn' if v >= 0.3 else 'good', d)
    if 'UNRATE' in S:
        v, d = last(S['UNRATE']); setk('unrate', v, f'{v:.1f}%', 'neutral', d)
    if 'BAMLH0A0HYM2' in S:
        v, d = last(S['BAMLH0A0HYM2']); setk('hy', v, f'{v:.2f} pp', 'bad' if v >= 5 else 'warn' if v >= 4 else 'good', d)
    if 'NFCI' in S:
        v, d = last(S['NFCI']); setk('nfci', v, f'{v:.2f}', 'bad' if v > 0 else 'good', d)
    if 'DFF' in S:
        v, d = last(S['DFF']); setk('fed', v, f'{v:.2f}%', None, d)
    if 'DGS10' in S:
        v, d = last(S['DGS10']); setk('ten', v, f'{v:.2f}%', 'bad' if v >= 5 else 'warn' if v >= 4.5 else 'neutral', d)
        fpe = byk.get('fpe', {}).get('value')
        if fpe:
            erp = 100 / float(fpe) - v
            setk('erp', round(erp, 2), f'{erp:+.2f} pp', 'bad' if erp < 1 else 'warn' if erp < 2.5 else 'good', d)
    if 'CPIAUCSL' in S:
        c = S['CPIAUCSL']; yoy = c.iloc[-1] / c[c.index <= c.index[-1] - pd.DateOffset(months=12)].iloc[-1] - 1
        setk('cpi', round(yoy * 100, 2), f'{yoy * 100:.1f}%', 'warn' if yoy > 0.025 else 'good', c.index[-1].strftime('%Y-%m-%d'))
    if fund_ok:
        f = pd.read_csv('work/fin.csv').dropna(subset=['Price', '52 Week High'])
        off = f.Price / f['52 Week High'] - 1
        n, n20 = len(f), int((off <= -0.20).sum())
        setk('breadth', round(n20 / n * 100, 1), f'{n20} of {n} ({n20 / n * 100:.0f}%)', 'warn' if n20 / n > 0.25 else 'neutral', NOW[:10])
    save('indicators', ind)

    # monthly rule-based signal (month-end data)
    m = sp.resample('ME').mean(); ma10 = m.rolling(10).mean()
    pm = m.index[-2] if m.index[-1].month == sp.index[-1].month else m.index[-1]   # last completed month
    mv = S.get('VIXCLS', pd.Series(dtype=float)).resample('ME').mean()
    nf = S.get('NFCI', pd.Series(dtype=float)).resample('ME').last()
    sa = S.get('SAHMREALTIME', pd.Series(dtype=float)).resample('ME').last().ffill()
    g = lambda s: float(s.get(pm, np.nan)) if len(s) else np.nan
    peak = float(sp[sp.index <= pm].max()); mdd = float(m[pm]) / peak - 1
    fear = (g(mv) >= 30) or (mdd <= -0.15)
    nf3 = float(nf.get(pm, np.nan) - nf.shift(3).get(pm, np.nan)) if len(nf) else np.nan
    stress = (g(sa) >= 0.5) or (g(nf) > 0)
    if float(m[pm]) < float(ma10[pm]) and stress and not (fear and nf3 < 0): sig = 'HOLD'
    elif fear: sig = 'BUY EXTRA'
    else: sig = 'BUY'
    reason = {'BUY': 'Trend is up and no recession or credit-stress warning is on. Keep buying your normal monthly amount.',
              'BUY EXTRA': 'Market is in a deep drop or panic without worsening credit stress. Deploy saved cash.',
              'HOLD': 'Downtrend plus a recession or credit-stress warning. Historically weak 12 months ahead.'}[sig]
    save('signal_now', [dict(signal=sig, reason=reason, month_used=pm.strftime('%Y-%m'), sp500_month_avg=round(float(m[pm]), 2),
                             ma10=round(float(ma10[pm]), 2), sahm=g(sa), nfci=g(nf), vix_month_avg=round(g(mv), 2), drawdown_pct=round(mdd * 100, 2),
                             spx_close=spx, ma50=round(ma50, 2), ma200=round(ma200, 2), ath=ath, ath_date=sp.idxmax().strftime('%Y-%m-%d'),
                             low52=float(yr.min()), high52=float(yr.max()))])

# ---------------------------------------------------------------- daily: markets table
def market_row(key, name, group, s, unit='', note=''):
    s = s.dropna()
    if s.empty: return None
    last_v, last_d = float(s.iloc[-1]), s.index[-1]
    def chg(days):
        past = s[s.index <= last_d - pd.Timedelta(days=days)]
        return round((last_v / float(past.iloc[-1]) - 1) * 100, 2) if len(past) else None
    ytd_base = s[s.index < pd.Timestamp(year=last_d.year, month=1, day=1)]
    yr = s[s.index > last_d - pd.Timedelta(days=365)]
    ma200 = float(s.iloc[-200:].mean()) if len(s) >= 200 else None
    wk = s.groupby(s.index.to_period('W')).tail(1).iloc[-53:]
    ath = float(s.max()); ath_date = s.idxmax()
    lr = None; first = s.index[0]
    if (last_d - first).days > 3650:
        yrs = (last_d - first).days / 365.25; lr = round(((last_v / float(s.iloc[0])) ** (1 / yrs) - 1) * 100, 1)
    eq = s / s.cummax() - 1
    return dict(key=key, name=name, group=group, last=round(last_v, 4 if last_v < 10 else 2), date=last_d.strftime('%Y-%m-%d'),
                w1=chg(7), w4=chg(28), ytd=round((last_v / float(ytd_base.iloc[-1]) - 1) * 100, 2) if len(ytd_base) else None, y1=chg(365),
                from_high_52w=round((last_v / float(yr.max()) - 1) * 100, 2), from_ath=round((last_v / ath - 1) * 100, 2), ath_date=ath_date.strftime('%Y-%m-%d'),
                trend='Above' if ma200 and last_v >= ma200 else 'Below' if ma200 else None, since=first.strftime('%Y'), cagr_since=lr,
                max_dd=round(float(eq.min()) * 100, 1), spark=[round(float(v), 2) for v in wk.values], unit=unit, note=note)
mk = []
if 'SP500' in S:
    mk.append(market_row('spx', 'S&P 500', 'US stocks', S['SP500'], 'pts'))
    if 'DEXUSEU' in S:
        fx = S['DEXUSEU'].reindex(S['SP500'].index).ffill()
        mk.append(market_row('spx_eur', 'S&P 500 in euros', 'US stocks', (S['SP500'] / fx).dropna(), 'pts', 'S&P 500 divided by EUR/USD: what a euro investor sees'))
for sid, key, name, group, unit, note in [('NASDAQCOM', 'nasdaq', 'Nasdaq Composite', 'US stocks', 'pts', ''), ('NASDAQ100', 'ndx', 'Nasdaq-100', 'US stocks', 'pts', 'Largest 100 non-financial Nasdaq stocks'),
                                          ('DJIA', 'dow', 'Dow Jones Industrial Average', 'US stocks', 'pts', '30 large US companies'), ('NIKKEI225', 'nikkei', 'Nikkei 225', 'World stocks', 'pts', 'Japan, in yen'),
                                          ('DEXUSEU', 'eurusd', 'Euro / US dollar', 'Currencies & commodities', '$ per €', 'Up = euro stronger, which lowers your US returns in euros'),
                                          ('DTWEXBGS', 'usd', 'US dollar index (broad)', 'Currencies & commodities', 'index', ''), ('DCOILBRENTEU', 'brent', 'Brent crude oil', 'Currencies & commodities', '$/barrel', ''),
                                          ('CBBTCUSD', 'btc', 'Bitcoin', 'Currencies & commodities', '$', 'Highly volatile; for context only')]:
    if sid in S:
        r = market_row(key, name, group, S[sid], unit, note)
        if r: mk.append(r)
if mk: save('markets', [m for m in mk if m])

# ---------------------------------------------------------------- weekly roll (Saturday run)
if args.weekly:
    need = ['SP500', 'VIXCLS', 'NFCI', 'SAHMREALTIME', 'T10Y3M']
    if not fund_ok or any(k not in S for k in need):
        log('ERROR weekly roll skipped: missing', [k for k in need if k not in S], 'fundamentals' if not fund_ok else '')
        sys.exit(1)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import indexpilot
    out, summary = indexpilot.run(S, D, args.research, 'work/fin.csv', 'work/cons.csv', log, args.offline)
    for n, obj in out.items(): save(n, obj)
    # archive this week's prices of the ranked stocks (our own price history for testing the picks later)
    try:
        yr_file = os.path.join(D, 'archive', f'prices_{summary["date"][:4]}.json'); os.makedirs(os.path.dirname(yr_file), exist_ok=True)
        arc = json.load(open(yr_file)) if os.path.exists(yr_file) else {}
        arc[summary['date']] = {r['ticker']: r['price'] for r in out['pick_rank'] if r.get('price') is not None}
        arc[summary['date']].update({r['etf']: r['price'] for r in out['index_rank']})
        json.dump(arc, open(yr_file, 'w'), separators=(',', ':')); log('archived prices for', len(arc[summary['date']]), 'tickers')
    except Exception as e: log('WARN price archive', e)
    b = summary['bt']
    open('work/summary.md', 'w').write(
        f"### Week of {summary['week_of']}\n\n- **Main index: {summary['pick']}** ({summary['etf']}){' (switched this week)' if summary['switched'] else ''}\n"
        f"- **Buy €{summary['amount']}** ({summary['tier']})\n- Signal strength **{summary['meter']:+d}** ({summary['label']})\n"
        f"- Demo account: €{summary['demo_value']} (MSCI World benchmark €{summary['demo_bench']}), {summary['trades']} trades this week\n"
        f"- Holdings: {', '.join(f'{t} {w}' for t, w, e in summary['positions'])}\n"
        f"- Extra profit record: last week €{summary['extra_week']}, total €{summary['extra_total']}\n"
        f"- Backtest of the pick since 2012: {b['cagr']}%/yr, worst fall {b['max_dd']}%\n")
log('done')
