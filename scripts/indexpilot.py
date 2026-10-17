"""IndexPilot weekly roll. Called by update.py --weekly (the Saturday run).

Each week it
  1. ranks six euro-listed index ETFs by their 52-week return and picks the main index
     by return per unit of risk (52-week return / 52-week volatility); the leader only replaces the current pick when
     its score is more than 0.25 higher (tested against the old 52-week-return rule: better on 2012-today ETF data
     and on 1990-2026 regional data),
  2. sets the weekly amount (EUR 40-200) and the market meter from the world market (MSCI World ETF)
     and US macro stress gauges (VIX, financial conditions, Sahm rule, yield curve),
  3. ranks the stocks of the picked index (value + momentum for the S&P 500, price momentum elsewhere),
  4. keeps the Extra profit record (3 longs / 3 shorts a week, weighted by inverse volatility) and runs the demo account:
     EUR 1,000 deposited every week, long only, 70% in the picked index ETF and 30% in its 3 strongest stocks,
  5. re-runs the 2012-today backtest of the whole routine on real ETF prices.

Prices: Yahoo Finance via the yfinance package (daily closes, adjusted). ETF history is cached in
research_data/etf_daily.csv so a failed download never loses data.
"""
import datetime as dt, json, math, os, time
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ETFS = [  # key, index, ETF symbol (Yahoo), fund name, ISIN, stock universe
    ('world', 'MSCI World', 'EUNL.DE', 'iShares Core MSCI World UCITS ETF (Acc)', 'IE00B4L5Y983', 'world'),
    ('us', 'S&P 500', 'SXR8.DE', 'iShares Core S&P 500 UCITS ETF (Acc)', 'IE00B5BMR087', 'sp500'),
    ('ndx', 'Nasdaq-100', 'SXRV.DE', 'iShares Nasdaq 100 UCITS ETF (Acc)', 'IE00B53SZB19', 'nasdaq100'),
    ('europe', 'MSCI Europe', 'EUNK.DE', 'iShares Core MSCI Europe UCITS ETF (Acc)', 'IE00B4K48X80', 'europe'),
    ('japan', 'MSCI Japan', 'EUNN.DE', 'iShares Core MSCI Japan IMI UCITS ETF (Acc)', 'IE00B4L5YX21', 'japan'),
    ('em', 'MSCI Emerging Markets', 'IEMA.AS', 'iShares MSCI EM UCITS ETF (Acc)', 'IE00B4L5YC18', 'emerging'),
]
EK = [e[0] for e in ETFS]
E = {e[0]: dict(key=e[0], index=e[1], etf=e[2], fund=e[3], isin=e[4], universe=e[5]) for e in ETFS}
BUFFER = 0.25          # a challenger's score (52-week return / 52-week volatility) must beat the current pick's by more than 0.25
OLD_BUFFER = 0.05      # previous rule: 52-week return, 5 percentage points
LIVE_START = '2026-10-09'   # first live weekly decision; earlier weeks are backtest
# The old rule (52-week return, 5-point buffer) had published MSCI Emerging Markets for this same week before the
# risk-adjusted rule replaced it; the site tells the user once, in that week only.
RULE_CHANGE = {'week': '2026-10-09', 'from': 'em'}
START = '2011-01-03'   # ETF prices before 2011 contain data errors (checked against the indexes)
CCY = {'.DE': 'EUR', '.AS': 'EUR', '.PA': 'EUR', '.BR': 'EUR', '.MC': 'EUR', '.MI': 'EUR', '.HE': 'EUR', '.L': 'GBp', '.SW': 'CHF',
       '.CO': 'DKK', '.ST': 'SEK', '.OL': 'NOK', '.T': 'JPY', '.TW': 'TWD', '.HK': 'HKD', '.KS': 'KRW', '.NS': 'INR', '.SA': 'BRL',
       '.SR': 'SAR', '.JO': 'ZAc', '.JK': 'IDR', '.MX': 'MXN'}
ccy = lambda t: next((v for k, v in CCY.items() if t.endswith(k)), 'USD')
yahoo = lambda t: t.replace('.', '-') if '.' in t and not any(t.endswith(k) for k in CCY) else t   # BRK.B -> BRK-B


def download(tickers, start, log, offline=None, chunk=80):
    """Daily adjusted closes, one column per ticker. Missing tickers are simply absent."""
    tickers = sorted(set(tickers))
    if offline:
        p = os.path.join(offline, 'prices.csv')
        df = pd.read_csv(p, index_col=0, parse_dates=True) if os.path.exists(p) else pd.DataFrame()
        return df[[t for t in tickers if t in df]]
    import yfinance as yf
    out = []
    for i in range(0, len(tickers), chunk):
        part = tickers[i:i + chunk]
        for attempt in range(3):
            try:
                d = yf.download([yahoo(t) for t in part], start=start, interval='1d', auto_adjust=True, progress=False, threads=True, group_by='column')
                c = d['Close'] if isinstance(d.columns, pd.MultiIndex) else d[['Close']].rename(columns={'Close': yahoo(part[0])})
                c.columns = [next((t for t in part if yahoo(t) == col), col) for col in c.columns]
                out.append(c.dropna(how='all', axis=1)); break
            except Exception as e:
                log(f'WARN price download {i}-{i + len(part)} attempt {attempt + 1}: {e}'); time.sleep(10 * (attempt + 1))
        time.sleep(1)
    if not out: return pd.DataFrame()
    df = pd.concat(out, axis=1)
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    log(f'prices: {df.shape[1]} of {len(tickers)} tickers, {df.index[0].date()} to {df.index[-1].date()}')
    return df


def weekly(df):
    """Last close of each week (weeks end Friday)."""
    return df.resample('W-FRI').last().ffill(limit=2)


def etf_prices(research, log, offline):
    cache = os.path.join(research, 'etf_daily.csv')
    old = pd.read_csv(cache, index_col=0, parse_dates=True) if os.path.exists(cache) else pd.DataFrame()
    new = download([E[k]['etf'] for k in EK], '2009-09-01', log, offline)
    if not new.empty:
        new = new.rename(columns={E[k]['etf']: k for k in EK})
        df = new.combine_first(old) if not old.empty else new
        df = df[[k for k in EK if k in df]].sort_index().dropna(how='all')   # Yahoo sometimes returns an empty row for a day not yet published
        if all(k in df for k in EK):
            df.round(4).to_csv(cache)
            return df
        log('WARN some ETF prices missing, using cache for them')
        return df.combine_first(old) if not old.empty else df
    if old.empty: raise RuntimeError('no ETF prices and no cache')
    log('WARN ETF download failed, using cached prices'); return old


# ------------------------------------------------------------------ rules
def scores(W, look=52):
    """52-week return and return per unit of risk (52-week return / annualised volatility of weekly moves)."""
    r = W / W.shift(look) - 1
    vol = np.log(W / W.shift(1)).rolling(look).std() * math.sqrt(52)
    return r, r / vol, vol


def buffered(score, buf):
    """Hold the current pick until another index's score beats it by more than buf."""
    score = score.dropna()
    held, path = None, []
    for d, row in score.iterrows():
        lead = row.idxmax()
        if held is None or row[lead] - row[held] > buf: held = lead
        path.append(held)
    return pd.Series(path, index=score.index)


def pick_path(W):
    """Week-by-week main index (current rule). Returns (52-week return, score, volatility, picks)."""
    r52, sc, vol = scores(W)
    ok = sc.dropna().index
    return r52.loc[ok], sc.loc[ok], vol.loc[ok], buffered(sc.loc[ok], BUFFER)


def amount_rule(w, trend, ath, vix, nfci, sahm):
    dd = w / ath - 1
    if vix < 30 and w < trend and (sahm >= 0.5 or nfci > 0): return 40, 'Stress', dd
    if vix >= 30 or dd <= -0.20: return 200, 'Bear market or panic', dd
    if dd <= -0.10: return 150, 'Correction', dd
    if dd <= -0.05: return 100, 'Dip', dd
    return 60, 'Normal', dd


clip = lambda x, a, b: max(a, min(b, x))


def meter_parts(w, trend, dd, vix, nfci, sahm, curve):
    return [
        ('World trend', 0.25, clip((w / trend - 1) / 0.05, -1, 1), f'MSCI World {(w / trend - 1) * 100:+.1f}% vs its 40-week line'),
        ('Discount from record', 0.20, clip(-dd / 0.15, 0, 1), f'MSCI World {dd * 100:.1f}% from its record (in euros)'),
        ('Fear (VIX)', 0.15, 1 if vix >= 30 else 0.5 if vix >= 20 else -0.5 if vix < 13 else 0, f'VIX {vix:.1f}'),
        ('Credit conditions (NFCI)', 0.15, -1 if nfci > 0 else -0.3 if nfci > -0.3 else 0.3, f'NFCI {nfci:.2f}'),
        ('Recession risk (Sahm)', 0.15, -1 if sahm >= 0.5 else -0.5 if sahm >= 0.3 else 0.3, f'Sahm {sahm:.2f}'),
        ('Yield curve', 0.10, -0.5 if curve < 0 else 0.2, f'10Y−3M {curve:+.2f}'),
    ]


meter_label = lambda m: 'Very strong market' if m >= 40 else 'Strong market' if m >= 15 else 'Mixed' if m > -10 else 'Weak market' if m > -25 else 'Very weak market'


def irr(flows, values_end):
    """Weekly money-weighted return. flows: amounts invested each week (positive), values_end: final value."""
    def npv(r):
        n = len(flows)
        return sum(f * (1 + r) ** (n - i) for i, f in enumerate(flows)) - values_end
    lo, hi = -0.02, 0.02
    for _ in range(200):
        mid = (lo + hi) / 2
        if npv(mid) > 0: hi = mid
        else: lo = mid
    return (1 + mid) ** 52 - 1


# ------------------------------------------------------------------ stock ranking
def sp500_rank(fin, cons):
    f = pd.read_csv(fin).merge(pd.read_csv(cons)[['Symbol', 'GICS Sector']], on='Symbol', how='left')
    f = f.dropna(subset=['Price', 'Market Cap', '52 Week High', '52 Week Low'])
    f = f[f['52 Week High'] > f['52 Week Low']].copy()
    f['sector'] = f['GICS Sector'].fillna('Unclassified')
    f['pe'] = f['Price/Earnings'].where(f['Price/Earnings'] > 0)
    f['ey'] = 1 / f.pe; f['sp'] = 1 / f['Price/Sales']; f['bp'] = (1 / f['Price/Book']).where(f['Price/Book'] > 0)
    f['range'] = (f.Price - f['52 Week Low']) / (f['52 Week High'] - f['52 Week Low'])
    f['off_high'] = f.Price / f['52 Week High'] - 1
    rk = lambda c: f.groupby('sector')[c].rank(pct=True).fillna(0)
    f['value'] = 0.5 * rk('ey') + 0.25 * rk('sp') + 0.25 * rk('bp')
    f['mom'] = f.groupby('sector')['range'].rank(pct=True)
    f['score'] = (0.5 * f.value + 0.5 * f.mom) * 100
    f = f.sort_values('score', ascending=False).reset_index(drop=True)
    f['rank'] = np.arange(1, len(f) + 1)
    note = lambda x: 'P/E unusually low: verify' if pd.notna(x.pe) and x.pe < 6 else 'Loss-making' if pd.isna(x.pe) else ''
    return [dict(rank=int(x['rank']), ticker=x.Symbol, company=x.Name, sector=x.sector, score=round(x.score, 1),
                 value=round(x.value * 100), momentum=round(x.mom * 100), pe=None if pd.isna(x.pe) else round(x.pe, 1),
                 off_52w_high=round(x.off_high * 100, 1), price=round(x.Price, 2), note=note(x)) for _, x in f.iterrows()]


def price_rank(members, px, date):
    """Price-only ranking: 50% 12-1 month momentum + 50% position in the 52-week range, as percentile ranks."""
    cut = pd.Timestamp(date)
    rows = []
    for m in members:
        t = m['ticker']
        if t not in px: continue
        s = px[t].dropna(); s = s[s.index <= cut]
        if len(s) < 230 or (cut - s.index[-1]).days > 10: continue
        w = weekly(s.to_frame()).iloc[:, 0].dropna()
        if len(w) < 53: continue
        p, p4, p52 = float(s.iloc[-1]), float(w.iloc[-5]), float(w.iloc[-53])
        y = s[s.index > cut - pd.Timedelta(days=365)]
        hi, lo = float(y.max()), float(y.min())
        if hi <= lo or p52 <= 0: continue
        # stale or reused ticker (e.g. PARA after Paramount became PSKY: 0.54 USD, -99% in a year): a big-index member below
        # 1 USD, or down over 95% in a year, is almost always broken data, not a real price
        if (ccy(t) == 'USD' and p < 1) or p / p52 - 1 < -0.95: continue
        dr = np.log(y / y.shift(1)).dropna()
        rows.append(dict(ticker=t, company=m['company'], country=m.get('country', ''), sector=m.get('sector', ''),
                         mom=p4 / p52 - 1, r1y=p / p52 - 1, range=(p - lo) / (hi - lo), off=p / hi - 1, price=p,
                         vol=float(dr.std() * math.sqrt(252)) if len(dr) > 100 else None))
    if not rows: return []
    df = pd.DataFrame(rows)
    df['score'] = 50 * df.mom.rank(pct=True) + 50 * df.range.rank(pct=True)
    df = df.sort_values('score', ascending=False).reset_index(drop=True)
    out = []
    for i, x in df.iterrows():
        note = 'Huge 1-year move: verify' if x.r1y > 3 else 'Down over 60% in a year' if x.r1y < -0.6 else ''
        out.append(dict(rank=i + 1, ticker=x.ticker, company=x.company, country=x.country, sector=x.sector, score=round(float(x.score), 1),
                        value=None, momentum=round(float(x.mom) * 100, 1), r1y=round(float(x.r1y) * 100, 1),
                        off_52w_high=round(float(x.off) * 100, 1), price=round(float(x.price), 2), currency=ccy(x.ticker), note=note,
                        vol=round(float(x.vol) * 100, 1) if pd.notna(x.vol) else None))
    return out


# ------------------------------------------------------------------ main
def run(S, D, research, fin, cons, log, offline=None):
    L = lambda n, d=None: json.load(open(os.path.join(D, n + '.json'))) if os.path.exists(os.path.join(D, n + '.json')) else d
    out = {}
    uni = json.load(open(os.path.join(HERE, 'universes.json')))

    # ---- ETF prices, weekly closes from 2011
    daily = etf_prices(research, log, offline)
    W = weekly(daily[daily.index >= START]).dropna()
    # A run before that Friday's close (e.g. a mid-week manual run) must not decide on an unfinished week.
    if not offline and W.index[-1].date() >= dt.datetime.now(dt.timezone.utc).date():
        log('latest week not finished yet; deciding on the previous Friday close'); W = W.iloc[:-1]
    date = W.index[-1]
    last_trading = daily.index[daily.index <= date][-1]
    # Friday's ETF closes not published yet (seen 2026-10-17: an all-empty Friday row at 09:48 UTC Saturday): don't decide on
    # Thursday's close under Friday's date. On Sunday (or later) a still-missing Friday is treated as an exchange holiday.
    if not offline and last_trading < date and dt.datetime.now(dt.timezone.utc).date() <= (date + pd.Timedelta(days=1)).date():
        raise RuntimeError(f"Friday {date.date()} ETF closes not published yet (latest {last_trading.date()}); retry later")
    dstr = last_trading.strftime('%Y-%m-%d')
    week_of = (last_trading.date() + dt.timedelta(days=(7 - last_trading.weekday()) % 7 or 7)).isoformat()
    log('IndexPilot week', dstr, '->', week_of)

    # ---- macro inputs, weekly (value known at each Friday)
    def wk(sid):
        s = S[sid]; return s.resample('W-FRI').last().ffill().reindex(W.index, method='ffill')
    mac = pd.DataFrame({k: wk(k) for k in ['VIXCLS', 'NFCI', 'SAHMREALTIME', 'T10Y3M']}).ffill()
    spx = S['SP500'].resample('W-FRI').last().reindex(W.index, method='ffill')

    # ---- full history: pick, amount, meter for every week
    r52, sc52, vol52, path = pick_path(W)
    world = W['world']; trend = world.rolling(40, min_periods=40).mean()
    ath = daily['world'].cummax().resample('W-FRI').last().reindex(W.index, method='ffill')
    hist = []
    for d in r52.index:
        if pd.isna(trend[d]) or mac.loc[d].isna().any(): continue
        v, nf, sa, cu = (float(mac.loc[d, k]) for k in ['VIXCLS', 'NFCI', 'SAHMREALTIME', 'T10Y3M'])
        amt, tier, dd = amount_rule(float(world[d]), float(trend[d]), float(ath[d]), v, nf, sa)
        m = round(100 * sum(wt * sc for _, wt, sc, _ in meter_parts(float(world[d]), float(trend[d]), dd, v, nf, sa, cu)))
        hist.append(dict(week=d.strftime('%Y-%m-%d'), pick=path[d], world=round(float(world[d]), 2), amount=amt, meter=m,
                         **{f'r52_{k}': round(float(r52.loc[d, k]) * 100, 1) for k in EK}, **{f'sc_{k}': round(float(sc52.loc[d, k]), 2) for k in EK}))
    H = pd.DataFrame(hist).set_index('week')

    # ---- this week's decision. Keep the pick the site published last week (live record), then apply the rule.
    stored = L('weekly_history', [])
    live_prev = [h for h in stored if h.get('pick') and LIVE_START <= h['week'] < H.index[-1]]
    prev_pick = live_prev[-1]['pick'] if live_prev else (path.iloc[-2] if len(path) > 1 else None)
    row = r52.loc[date]; srow = sc52.loc[date]; vrow = vol52.loc[date]; leader = srow.idxmax()
    pick = leader if prev_pick is None or srow[leader] - srow[prev_pick] > BUFFER else prev_pick
    pick = os.environ.get('IP_FORCE_PICK') or pick   # testing only
    switched = prev_pick is not None and pick != prev_pick
    H.loc[H.index[-1], 'pick'] = pick
    # history: keep published live rows, fill the rest from the backtest
    pub = {h['week']: h for h in stored if h.get('pick') and h['week'] >= LIVE_START}
    weekly_history = [dict(r, week=w, pick=pub[w]['pick'] if w in pub and w != H.index[-1] else r['pick']) for w, r in H.to_dict('index').items()]

    last = hist[-1]
    v, nf, sa, cu = (float(mac.iloc[-1][k]) for k in ['VIXCLS', 'NFCI', 'SAHMREALTIME', 'T10Y3M'])
    wv, tr, at = float(world.iloc[-1]), float(trend.iloc[-1]), float(ath.iloc[-1])
    amount, tier, dd = amount_rule(wv, tr, at, v, nf, sa)
    parts = meter_parts(wv, tr, dd, v, nf, sa, cu)
    meter = round(100 * sum(w * s for _, w, s, _ in parts)); label = meter_label(meter)
    meter_rows = [dict(component=c, weight=round(w * 100), score=round(s, 2), contribution=round(100 * w * s, 1), reading=t) for c, w, s, t in parts]
    meter_rows.append(dict(component='Total', weight=100, score=None, contribution=meter, reading=label))

    # ---- index table
    def chg(k, n): return round((float(W[k].iloc[-1]) / float(W[k].iloc[-1 - n]) - 1) * 100, 1)
    idx_rows = []
    order = srow.sort_values(ascending=False).index.tolist()
    for k in EK:
        s = W[k]; y = daily[k][daily.index > daily.index[-1] - pd.Timedelta(days=365)]
        t40 = float(s.iloc[-40:].mean())
        status = "This week's pick" if k == pick else ('Best score, but inside the buffer' if k == leader else '')
        idx_rows.append(dict(rank=order.index(k) + 1, key=k, index=E[k]['index'], etf=E[k]['etf'], fund=E[k]['fund'], isin=E[k]['isin'],
                             price=round(float(s.iloc[-1]), 2), r52=round(float(row[k]) * 100, 1), r26=chg(k, 26), r13=chg(k, 13), r4=chg(k, 4), r1=chg(k, 1),
                             score=round(float(srow[k]), 2), gap_to_pick=round(float(srow[k]) - float(srow[pick]), 2), from_high_52w=round((float(s.iloc[-1]) / float(y.max()) - 1) * 100, 1),
                             trend='Above' if float(s.iloc[-1]) >= t40 else 'Below', vol=round(float(np.log(s / s.shift(1)).iloc[-52:].std() * math.sqrt(52) * 100), 1),
                             spark=[round(float(x), 2) for x in s.iloc[-53:].values], status=status))
    idx_rows.sort(key=lambda r: r['rank'])
    out['index_rank'] = idx_rows

    # ---- stocks of the picked index
    sp_rows = sp500_rank(fin, cons)
    sp_members = [dict(ticker=r['ticker'], company=r['company'], sector=r['sector'], country='US') for r in sp_rows]
    U = E[pick]['universe']
    members = {'sp500': sp_members, 'nasdaq100': uni['nasdaq100']['members'], 'europe': uni['europe']['members'],
               'japan': uni['japan']['members'], 'emerging': uni['emerging']['members']}
    members['world'] = sp_members + members['europe'] + members['japan'] + members['emerging']
    uname = {'sp500': 'S&P 500 members', 'world': 'S&P 500 + Europe + Japan + emerging-market lists',
             **{k: uni[k]['name'] for k in ['nasdaq100', 'europe', 'japan', 'emerging']}}[U]
    # ---- extra profit (paper record of the weekly 3 longs / 3 shorts) ----------------------------
    # and the demo account (EUR 1,000 portfolio: 70% picked index ETF + 30% in its 3 strongest stocks)
    old_pos = L('demo_positions', []) or []
    if old_pos and old_pos[0].get('v') == 2 and not os.path.exists(os.path.join(D, 'extra_positions.json')):
        # migration from the weekly-bet demo: its stock leg becomes the Extra profit record, the demo restarts as a portfolio
        L_extra_pos = [p for p in old_pos if p.get('leg') == 'Stocks']
        L_extra_led = [l for l in (L('demo_ledger', []) or []) if l.get('leg') in ('Stocks', 'Account')]
    else:
        L_extra_pos = L('extra_positions', []) or []
        L_extra_led = L('extra_ledger', []) or []
    state = L('demo_state', {}) or {}
    if state.get('v') != 3: state = {}
    demo_rerun = bool(state.get('last_date') == dstr and state.get('prev'))
    if demo_rerun: state = state['prev']   # same-day rerun: redo this week from last week's state
    held_t = [h['ticker'] for h in state.get('holdings', []) if h['leg'] == 'Stocks']
    # Free Money paper variants (long only), state kept between runs; a same-day rerun starts again from last week's state
    VS = L('free_money_variants_state', None) or {}
    if VS.get('asof') == dstr and 'prev' in VS: VS = VS['prev']
    VS_prev = json.loads(json.dumps(VS))
    var_t = [p_['ticker'] for k_ in ('A', 'B') for p_ in (VS.get(k_) or {}).get('pos', [])]
    need = [m['ticker'] for m in members[U]] + [p['ticker'] for p in L_extra_pos] + held_t + var_t
    px = download(need, (last_trading - pd.Timedelta(days=430)).strftime('%Y-%m-%d'), log, offline)
    if U == 'sp500':
        pr = {r['ticker']: r for r in price_rank(members[U], px, dstr)}
        rows = []
        for r in sp_rows:
            p = pr.get(r['ticker'], {})
            rows.append(dict(rank=r['rank'], ticker=r['ticker'], company=r['company'], country='US', sector=r['sector'], score=r['score'], value=r['value'],
                             momentum=p.get('momentum'), r1y=p.get('r1y'), off_52w_high=r['off_52w_high'], price=p.get('price', r['price']), currency='USD', note=r['note'], vol=p.get('vol')))
        method = 'Value + momentum (S&P 500 fundamentals): 50% cheapness vs sector on earnings, sales and book, 50% position in the 52-week range'
    else:
        rows = price_rank(members[U], px, dstr)
        method = 'Price momentum: 50% 12-1 month return, 50% position in the 52-week range (no free fundamentals outside the US)'
    if len(rows) < 20: raise RuntimeError(f'only {len(rows)} stocks ranked for {U}')
    keep = rows if len(rows) <= 300 else rows[:100] + rows[-100:]
    for r in keep: r['side'] = 'Top' if r['rank'] <= len(rows) / 2 else 'Bottom'
    out['pick_rank'] = keep
    log(f'ranked {len(rows)} stocks in {uname}')

    # ---- prices for booking
    etf_px = {E[k]['etf']: float(daily[k][daily.index <= last_trading].dropna().iloc[-1]) for k in EK}
    fin_px = {r['ticker']: r['price'] for r in sp_rows}
    rank_of = {r['ticker']: r for r in rows}
    def last_px(t):
        if t == 'S&P 500': return float(spx.iloc[-1])
        if t in etf_px: return etf_px[t]
        if t in px and px[t].dropna().size and (last_trading - px[t].dropna().index[-1]).days <= 10: return float(px[t].dropna().iloc[-1])
        return fin_px.get(t)
    def hi_since(t, since):
        if t in px:
            s_ = px[t].dropna(); s_ = s_[(s_.index >= pd.Timestamp(since)) & (s_.index <= last_trading)]
            if len(s_): return float(s_.max())
        return None
    # FX: units of each currency per euro (yfinance EURxxx=X), for valuing stocks in euros
    ccys = sorted({ccy(t) for t in held_t + [r['ticker'] for r in rows[:10]]} - {'EUR'})
    fxd = download([f"EUR{ {'GBp': 'GBP', 'ZAc': 'ZAR'}.get(c, c) }=X" for c in ccys], (last_trading - pd.Timedelta(days=20)).strftime('%Y-%m-%d'), log, offline) if ccys else pd.DataFrame()
    def fx(c):
        if c == 'EUR': return 1.0
        base = {'GBp': 'GBP', 'ZAc': 'ZAR'}.get(c, c)
        col = f'EUR{base}=X'
        v = float(fxd[col].dropna().iloc[-1]) if col in fxd and fxd[col].dropna().size else None
        if v is None: log('WARN no FX for', c); return None
        return v * (100 if c in ('GBp', 'ZAc') else 1)
    COST = 0.002   # 0.2% per trade: spread + currency exchange (commission-free broker assumed)

    # weights for a group of stocks: inverse volatility (calmer stocks get more), whole percents summing to 100
    def invw(rs):
        vs = [r.get('vol') for r in rs]
        med = float(np.median([v for v in vs if v])) if any(vs) else 30.0
        raw = [1 / (v or med) for v in vs]; tot = sum(raw)
        w = [round(100 * x / tot) for x in raw]
        if w: w[w.index(max(w))] += 100 - sum(w)
        return w

    # ---- Extra profit: weekly 3 longs / 3 shorts of the main index, closed every week.
    #      Each side is split by inverse volatility; results are tracked in % of the stake (shown per EUR 500: 250 long + 250 short).
    STAKE_SIDE = 250.0
    extra_pos, extra_led = L_extra_pos, L_extra_led
    if extra_pos and extra_pos[0]['entry_date'] == dstr and 'weight' not in extra_pos[0]:
        for side in ('Long', 'Short'):   # same-day upgrade: add weights to this week's picks
            grp = [p for p in extra_pos if p['side'] == side]
            for p, w in zip(grp, invw([rank_of.get(p['ticker'], {}) for p in grp])):
                p['weight'] = w; p['euros'] = round(STAKE_SIDE * w / 100, 2)
    if extra_pos and extra_pos[0]['entry_date'] == dstr and not all(f"in {E[pick]['index']} " in p.get('reason', '') for p in extra_pos):
        log('extra profit: same-day picks were for another index; rebuilding them for', E[pick]['index'])
        extra_pos = []   # nothing was closed yet: this week's picks are simply re-chosen
    if extra_pos and extra_pos[0]['entry_date'] == dstr and any(p['ticker'] not in rank_of for p in extra_pos):
        log('extra profit: a same-day pick is no longer ranked (bad data filtered); re-choosing this week\'s picks')
        extra_pos = []
    if not (extra_pos and extra_pos[0]['entry_date'] == dstr):
        for p in extra_pos:
            xp = last_px(p['ticker']); n = ''
            if xp is None: xp, n = p['entry_price'], 'No price: closed flat'
            sgn = 1 if p['side'] == 'Long' else -1
            ret = sgn * (xp / p['entry_price'] - 1)
            extra_led.append(dict(id=f"{p['week_of']}-{p['ticker']}", week_of=p['week_of'], closed_on=dstr, leg='Stocks', ticker=p['ticker'],
                                  side=p['side'], weight=p.get('weight', 33), euros=p['euros'], entry_price=p['entry_price'], exit_price=round(xp, 4 if xp < 10 else 2),
                                  return_pct=round(ret * 100, 2), pnl_eur=round(p['euros'] * ret, 2), note=n))
        extra_pos = []
        longs = [r for r in rows if not r['note']][:3]
        shorts = [r for r in rows[::-1] if 'verify' not in r['note']][:3]
        for grp, side in [(longs, 'Long'), (shorts, 'Short')]:
            for r, w in zip(grp, invw(grp)):
                extra_pos.append(dict(v=2, id=f"{week_of}-{r['ticker']}", week_of=week_of, entry_date=dstr, leg='Stocks', ticker=r['ticker'], company=r['company'],
                                      side=side, weight=w, euros=round(STAKE_SIDE * w / 100, 2), entry_price=r['price'], currency=r.get('currency', 'USD'), vol=r.get('vol'),
                                      reason=f"Rank {r['rank']} of {len(rows)} in {E[pick]['index']} (score {r['score']})"))
    for p in extra_pos:
        p['vol'] = p.get('vol') or rank_of.get(p['ticker'], {}).get('vol')
    # ---- Free Money variants, tracked live from LIVE_START as % of a 100 stake, 0.2% per trade:
    #   A "keepers": hold the 3 strongest stocks; keep each while it stays in the top 20% of the ranking; sell if it drops out
    #     or falls 25% below its highest weekly close since bought; refill to 3 from the top (weights: inverse volatility).
    #   B "keepers + trend guard": the same, but no new buys while MSCI World is below its 40-week line.
    top_set = {r['ticker'] for r in rows[:max(3, int(round(len(rows) * 0.2)))]}
    cands = [r for r in rows if not r['note']]
    guard_on = bool(float(world.iloc[-1]) < float(trend.iloc[-1]))
    def vstep(st, use_guard):
        st = json.loads(json.dumps(st)) if st else {'cash': 100.0, 'pos': [], 'hist': []}
        for p_ in st['pos']:
            xp = last_px(p_['ticker'])
            if xp: p_['value'] *= xp / p_['last']; p_['last'] = xp; p_['peak'] = max(p_['peak'], xp)
        kept, sold = [], []
        for p_ in st['pos']:
            if p_['ticker'] not in top_set or p_['last'] <= 0.75 * p_['peak']: st['cash'] += p_['value'] * (1 - COST); sold.append(p_['ticker'])
            else: kept.append(p_)
        st['pos'], bought = kept, []
        if not (use_guard and guard_on):
            new = [r for r in cands if r['ticker'] not in {p_['ticker'] for p_ in kept} and r.get('price')][:3 - len(kept)]
            if new and st['cash'] > 0.01:
                budget = st['cash']
                for r, w in zip(new, invw(new)):
                    amt = budget * w / 100; st['cash'] -= amt; bought.append(r['ticker'])
                    st['pos'].append(dict(ticker=r['ticker'], company=r['company'], currency=r.get('currency', 'USD'), since=dstr, entry=r['price'], last=r['price'], peak=r['price'], value=amt * (1 - COST)))
        tot = st['cash'] + sum(p_['value'] for p_ in st['pos'])
        st['hist'] = [h for h in st['hist'] if h['date'] != dstr] + [dict(date=dstr, pct=round(tot - 100, 2), bought=bought, sold=sold, guard=guard_on if use_guard else None)]
        return st
    if dstr >= LIVE_START:
        VA, VB = vstep(VS.get('A'), False), vstep(VS.get('B'), True)
        out['free_money_variants_state'] = dict(asof=dstr, prev=VS_prev, A=VA, B=VB)
        hold_rows = []
        for key_, st_ in (('A', VA), ('B', VB)):
            tot = st_['cash'] + sum(p_['value'] for p_ in st_['pos'])
            for p_ in st_['pos']:
                hold_rows.append(dict(strategy=key_, ticker=p_['ticker'], company=p_['company'], weight=round(p_['value'] / tot * 100), since=p_['since'],
                                      return_pct=round((p_['last'] / p_['entry'] - 1) * 100, 1), price=p_['last'], currency=p_['currency'],
                                      action='Buy' if p_['since'] == dstr else 'Keep'))
            last_h = st_['hist'][-1] if st_['hist'] else {}
            prev_pos = {p_['ticker']: p_ for p_ in (VS.get(key_) or {}).get('pos', [])}
            for t_ in last_h.get('sold', []):
                q_ = prev_pos.get(t_, {})
                hold_rows.append(dict(strategy=key_, ticker=t_, company=q_.get('company', t_), weight=0, since=q_.get('since'), return_pct=None, price=None, currency=q_.get('currency'), action='Sell'))
            if st_['cash'] / tot > 0.02: hold_rows.append(dict(strategy=key_, ticker='Cash', company='Waiting (trend guard)' if key_ == 'B' and guard_on else 'Cash', weight=round(st_['cash'] / tot * 100), since=None, return_pct=None, price=None, currency='EUR', action='Hold cash'))
        out['free_money_holdings'] = hold_rows
    else:
        VA = VB = None
    if not extra_led: extra_led = [dict(id='open', week_of=dstr, closed_on=dstr, leg='Account', ticker='', side='', euros=0, entry_price=0, exit_price=0, return_pct=0, pnl_eur=0, note='Record started')]
    out['extra_positions'], out['extra_ledger'] = extra_pos, extra_led

    # ---- Demo account: EUR 1,000 deposited every week, long only, profits stay in
    #   core  70%: this week's main-index ETF; switched only when the pick switches; new money tops it up to 70%;
    #              trimmed back to 70% only if it grows above 80%
    #   stocks 30%: the 3 strongest stocks of the picked index, split by inverse volatility; a stock is kept while it stays in
    #               the top 20% of the ranking and has not fallen 25% from its highest close since purchase; replaced otherwise
    CORE, STOCKS, NSLOT, BAND, KEEP, TRAIL, DEPOSIT = 0.70, 0.30, 3, 0.10, 0.20, 0.25, 1000.0
    bench_px = etf_px[E['world']['etf']]
    led = (L('demo_ledger', []) or []) if state else []
    led = [l for l in led if l.get('v') == 3 and not (demo_rerun and l.get('date') == dstr)]
    val_rows = (L('demo_value', []) or []) if state else []
    opening = not state
    if opening:
        state = dict(v=3, start=dstr, cash=DEPOSIT, invested=DEPOSIT, holdings=[], bench_ticker=E['world']['etf'], bench_units=DEPOSIT / bench_px, last_date=None)
        led = [dict(v=3, id=f'{dstr}-deposit', date=dstr, action='Deposit', leg='Account', ticker='', company='', side='', shares=0, price=0, currency='EUR',
                    value_eur=DEPOSIT, cost_eur=0, pnl_eur=0, return_pct=None, note='Weekly deposit (€1,000 every Friday close)')]
        log('demo: opened with EUR 1,000 on', dstr)
    if 'invested' not in state:   # account opened before weekly deposits existed
        state['invested'] = DEPOSIT; state['bench_units'] = DEPOSIT / state['bench_start']
        for l in led:
            if l['action'] == 'Open account': l.update(action='Deposit', note='Weekly deposit (€1,000 every Friday close)')
    H_ = state['holdings']
    def value_of(h):
        p_ = last_px(h['ticker']); f_ = fx(h['currency'])
        if p_ is None or f_ is None or not (p_ > 0 and f_ > 0): p_, f_ = h.get('last_price', h['entry_price']), h.get('last_fx', h['entry_fx'])
        h['last_price'], h['last_fx'] = p_, f_
        return h['shares'] * p_ / f_
    def book(action, h, shares, note, p_=None, f_=None):
        p_ = p_ or h['last_price']; f_ = f_ or h['last_fx']; v_ = shares * p_ / f_; c_ = v_ * COST
        pnl = v_ - shares * h['entry_price'] / h['entry_fx'] if action == 'Sell' else 0
        led.append(dict(v=3, id=f"{dstr}-{action}-{h['ticker']}-{len(led)}", date=dstr, action=action, leg=h['leg'], ticker=h['ticker'], company=h['company'], side='Long',
                        shares=round(shares, 6), price=round(p_, 4), currency=h['currency'], value_eur=round(v_, 2), cost_eur=round(c_, 2),
                        pnl_eur=round(pnl - c_, 2), return_pct=round((p_ / f_) / (h['entry_price'] / h['entry_fx']) * 100 - 100, 2) if action == 'Sell' else None, note=note))
        return v_, c_
    def sell(h, shares, note):
        v_, c_ = book('Sell', h, shares, note); state['cash'] += v_ - c_; h['shares'] -= shares
    def buy(leg, ticker, company, ccy_, euros, note):
        p_ = last_px(ticker); f_ = fx(ccy_)
        euros = min(euros, state['cash'] / (1 + COST))
        if not p_ or not f_ or not (p_ > 0 and f_ > 0 and euros >= 1): return   # also rejects NaN
        sh = euros / (p_ / f_)
        h = next((x for x in H_ if x['ticker'] == ticker), None)
        if h is None:
            h = dict(leg=leg, ticker=ticker, company=company, currency=ccy_, shares=0.0, entry_price=p_, entry_fx=f_, entry_date=dstr, last_price=p_, last_fx=f_, high=p_)
            H_.append(h)
        book('Buy', h, sh, note, p_, f_)
        cost_old = h['shares'] * h['entry_price'] / h['entry_fx']
        h['entry_price'] = (h['shares'] * h['entry_price'] + sh * p_) / (h['shares'] + sh)
        h['shares'] += sh
        h['entry_fx'] = h['shares'] * h['entry_price'] / (cost_old + euros)
        state['cash'] -= euros * (1 + COST)
    if state.get('last_date') != dstr:
        state['prev'] = None if opening else json.loads(json.dumps({k: v for k, v in state.items() if k != 'prev'}))
        for h in H_: value_of(h)
        if not opening:
            state['cash'] += DEPOSIT; state['invested'] += DEPOSIT; state['bench_units'] += DEPOSIT / bench_px
            led.append(dict(v=3, id=f'{dstr}-deposit', date=dstr, action='Deposit', leg='Account', ticker='', company='', side='', shares=0, price=0, currency='EUR',
                            value_eur=DEPOSIT, cost_eur=0, pnl_eur=0, return_pct=None, note='Weekly deposit (€1,000 every Friday close)'))
        e = E[pick]
        for h in [h for h in H_ if h['leg'] == 'Index' and h['ticker'] != e['etf']]:
            sell(h, h['shares'], f"Pick switched to {e['index']}")
        top_n = max(NSLOT, int(math.ceil(KEEP * len(rows))))
        for h in [h for h in H_ if h['leg'] == 'Stocks']:
            r = rank_of.get(h['ticker']); hi = max(h.get('high', h['entry_price']), hi_since(h['ticker'], h['entry_date']) or 0)
            h['high'] = hi
            if r is None: sell(h, h['shares'], f"Not in this week's index ({e['index']})")
            elif r['rank'] > top_n: sell(h, h['shares'], f"Fell to rank {r['rank']} (outside top {top_n})")
            elif h['last_price'] <= hi * (1 - TRAIL): sell(h, h['shares'], 'Trailing stop: 25% below its high since purchase')
        H_[:] = [h for h in H_ if h['shares'] > 1e-9]
        eq = state['cash'] + sum(value_of(h) for h in H_)
        # core: buy, top up with new money, or trim if above 80%
        cv = sum(value_of(h) for h in H_ if h['leg'] == 'Index')
        core_name = f"{e['index']} ETF ({e['fund']})"
        if cv > (CORE + BAND) * eq:
            h = next(h for h in H_ if h['leg'] == 'Index'); sell(h, h['shares'] * (cv - CORE * eq) / cv, 'Trim back to 70%')
        elif cv < CORE * eq:
            buy('Index', e['etf'], core_name, 'EUR', CORE * eq - cv, 'Core: main index' if cv == 0 else 'Core: weekly deposit')
        # stocks: keep the survivors, fill empty slots from the top of the ranking, top each up to its inverse-volatility target
        held = [h for h in H_ if h['leg'] == 'Stocks']
        cand = [rank_of[h['ticker']] for h in held] + [r for r in rows if not r['note'] and r['ticker'] not in {h['ticker'] for h in held}]
        chosen = cand[:NSLOT]
        for r, w in zip(chosen, invw(chosen)):
            have = next((h for h in H_ if h['ticker'] == r['ticker']), None)
            gap = STOCKS * eq * w / 100 - (value_of(have) if have else 0)
            if gap > 1: buy('Stocks', r['ticker'], r['company'], r.get('currency', 'USD'), gap, f"{w}% of the stock part · rank {r['rank']} of {len(rows)} in {e['index']}")
        if state['cash'] > 5: buy('Index', e['etf'], core_name, 'EUR', state['cash'] / (1 + COST), 'Core: leftover cash')
        state['last_date'] = dstr
    # positions view and weekly value
    eq = state['cash'] + sum(value_of(h) for h in H_)
    bench = state['bench_units'] * bench_px
    positions = []
    for h in H_:
        v_ = value_of(h); cost_ = h['shares'] * h['entry_price'] / h['entry_fx']
        r = rank_of.get(h['ticker'], {})
        positions.append(dict(v=3, id=f"{h['entry_date']}-{h['ticker']}", leg=h['leg'], ticker=h['ticker'], company=h['company'], side='Long', currency=h['currency'],
                              shares=round(h['shares'], 6), entry_date=h['entry_date'], entry_price=round(h['entry_price'], 4), price=round(h['last_price'], 4),
                              euros=round(v_, 2), weight=round(v_ / eq * 100, 1), pnl_eur=round(v_ - cost_, 2), return_pct=round((v_ / cost_ - 1) * 100, 2) if cost_ else 0,
                              rank=r.get('rank'), reason=('Core: main index' if h['leg'] == 'Index' else f"Rank {r.get('rank', '—')} now")))
    positions.sort(key=lambda p: (p['leg'] != 'Index', -p['euros']))
    val_rows = [r for r in val_rows if r['date'] != dstr] + [dict(date=dstr, value=round(eq, 2), invested=round(state['invested'], 2), benchmark=round(bench, 2),
                cash=round(state['cash'], 2), core=round(sum(p['euros'] for p in positions if p['leg'] == 'Index'), 2),
                stocks=round(sum(p['euros'] for p in positions if p['leg'] == 'Stocks'), 2), pick=pick)]
    out['demo_state'], out['demo_positions'], out['demo_ledger'], out['demo_value'] = state, positions, led, val_rows
    ledger = led
    # ---- backtest 2012-today on the ETF prices (weekly, in euros)
    R = W.pct_change().shift(-1).reindex(H.index.map(pd.Timestamp))   # next week's return, decided at this week's close
    R.index = H.index
    picks = H['pick']
    def on_h(sq): sq = sq.reindex(pd.to_datetime(H.index)); sq.index = H.index; return sq
    nobuf = on_h(buffered(sc52, 0.0))
    old = on_h(buffered(r52, OLD_BUFFER))
    def series(kind):
        if kind in EK: return R[kind]
        if kind == 'equal': return R[EK].mean(axis=1)
        if kind == 'pick': return pd.Series([R.loc[d, k] for d, k in picks.items()], index=H.index)
        if kind == 'nobuf': return pd.Series([R.loc[d, k] for d, k in nobuf.items()], index=H.index)
        if kind == 'old': return pd.Series([R.loc[d, k] for d, k in old.items()], index=H.index)
    def tw(r):
        r = r.dropna(); eq = (1 + r).cumprod(); yrs = len(r) / 52.18
        return eq, round((eq.iloc[-1] ** (1 / yrs) - 1) * 100, 1), round(float((eq / eq.cummax() - 1).min()) * 100, 1), round(float(r.std() * math.sqrt(52) * 100), 1)
    names = {'pick': 'IndexPilot pick (return per unit of risk)', 'old': 'Previous rule (52-week return, 5-point buffer)', 'nobuf': 'Best score each week, no buffer', 'equal': 'All six, equal weight',
             **{k: f"Hold {E[k]['index']}" for k in EK}}
    bt, curves = [], {}
    for k in ['pick', 'old', 'nobuf', 'equal'] + EK:
        eq, c, mdd, vol = tw(series(k)); curves[k] = eq
        sw = None
        if k in ('pick', 'nobuf', 'old'):
            sq = {'pick': picks, 'nobuf': nobuf, 'old': old}[k]
            sw = round(float((sq != sq.shift(1)).iloc[1:].sum()) / (len(sq) / 52.18), 1)
        bt.append(dict(key=k, strategy=names[k], cagr=c, max_dd=mdd, vol=vol, switches_per_year=sw))
    # money-weighted: the weekly amounts actually bought
    amts = H['amount'].astype(float); flat = float(amts.mean())
    def mw(kind, amounts, switch_all):
        hold = {k: 0.0 for k in EK}; flows = []; path_ = []
        hix = list(H.index)
        for i, d in enumerate(hix[:-1]):
            target = picks[d] if kind == 'pick' else kind
            if switch_all and kind == 'pick':
                tot = sum(hold.values()); hold = {k: 0.0 for k in EK}; hold[target] = tot
            hold[target] += amounts[d]; flows.append(amounts[d])
            for k in EK: hold[k] *= 1 + (R.loc[d, k] if pd.notna(R.loc[d, k]) else 0)
            path_.append((hix[i + 1], sum(flows), sum(hold.values())))
        val = sum(hold.values())
        return round(sum(flows)), round(val), round(irr(flows, val) * 100, 1), path_
    mwrows, mwpaths = [], {}
    for key_, label_, kind, amounts, sw in [('flat_world', 'Flat amount into MSCI World', 'world', pd.Series(flat, index=H.index), False),
                                            ('rule_world', 'Weekly rule into MSCI World', 'world', amts, False),
                                            ('rule_us', 'Weekly rule into S&P 500', 'us', amts, False),
                                            ('rule_pick', 'Weekly rule into the pick, new money only', 'pick', amts, False),
                                            ('rule_pick_move', 'Weekly rule into the pick, move everything on a switch', 'pick', amts, True)]:
        inv, val, r_, path_ = mw(kind, amounts, sw)
        mwrows.append(dict(key=key_, plan=label_, invested=inv, value=val, irr=r_)); mwpaths[key_] = path_
    out['ip_backtest'] = bt
    # rule variants that were tested (same data, same costs: none); halves show whether a result holds in both periods
    def var_ret(sq, trend_fb=None):
        r = pd.Series([R.loc[d, k] for d, k in sq.items()], index=H.index)
        if trend_fb:
            ma = W.rolling(40).mean()
            r = pd.Series([R.loc[d, trend_fb] if float(W.loc[pd.Timestamp(d), k]) < float(ma.loc[pd.Timestamp(d), k]) else R.loc[d, k] for d, k in sq.items()], index=H.index)
        return r.dropna()
    def var_stats(sq, trend_fb=None, r=None):
        r = var_ret(sq, trend_fb) if r is None else r.dropna()
        sq = sq if sq is not None else pd.Series(0, index=r.index)
        yrs = len(r) / 52.18; eq = (1 + r).cumprod()
        cg = lambda x: round((float((1 + x).prod()) ** (52.18 / len(x)) - 1) * 100, 1)
        return dict(cagr=round((eq.iloc[-1] ** (1 / yrs) - 1) * 100, 1), max_dd=round(float((eq / eq.cummax() - 1).min()) * 100, 1),
                    sharpe=round(float(r.mean() / r.std() * math.sqrt(52)), 2), switches_per_year=round(float((sq != sq.shift(1)).iloc[1:].sum()) / yrs, 1),
                    first_half=cg(r[r.index < '2019-01-01']), second_half=cg(r[r.index >= '2019-01-01']))
    r26 = W / W.shift(26) - 1
    vrows = [('riskadj', 'Return per unit of risk, 0.25 buffer (current rule)', picks, None), ('old', '52-week return, 5-point buffer (previous rule)', old, None),
             ('ret_nobuf', '52-week return, no buffer', on_h(buffered(r52, 0.0)), None), ('ret26', '26-week return, 5-point buffer', on_h(buffered(r26.dropna(), OLD_BUFFER)), None),
             ('ret_buf10', '52-week return, 10-point buffer', on_h(buffered(r52, 0.10)), None), ('riskadj_nobuf', 'Return per unit of risk, no buffer', nobuf, None),
             ('trend', '52-week return, 5-point buffer, MSCI World when below its 40-week line', old, 'world')]
    out['ip_variants'] = [dict(key=k, rule=nm, **var_stats(sq.ffill().bfill(), fb)) for k, nm, sq, fb in vrows]
    out['ip_buying'] = mwrows
    step = max(1, len(H) // 300)
    out['ip_growth'] = [dict(date=d, **{k: round(float(curves[k].get(d, np.nan)), 4) for k in ['pick', 'world', 'us', 'ndx', 'europe', 'equal']})
                        for i, d in enumerate(H.index[:-1]) if i % step == 0 or i == len(H) - 2]
    # ---- Simulation tab: every strategy on the same weekly ETF data (backtest, no costs). Value at the END of each week,
    # so the series starts at 1.0 on the first decision Friday and each point uses only decisions made a week earlier.
    sg4 = lambda v: None if v is None or not np.isfinite(v) else float(f'{v:.4g}')
    hix = list(H.index)
    vret = {k: var_ret(sq.ffill().bfill(), fb) for k, nm, sq, fb in vrows}
    vret['pick'] = vret.pop('riskadj')
    rets = {**vret, 'equal': series('equal').dropna(), **{k: series(k).dropna() for k in EK}}
    order = ['pick', 'old', 'ret_buf10', 'ret_nobuf', 'ret26', 'riskadj_nobuf', 'trend', 'equal'] + EK
    rets = {k: rets[k] for k in order if k in rets}
    vnames = {('pick' if k == 'riskadj' else k): nm for k, nm, sq, fb in vrows}
    groups = {'pick': 'Current rule', 'old': 'Previous rule', 'equal': 'Benchmark', **{k: 'Tested variant' for k in vret if k not in ('pick', 'old')}, **{k: 'Hold one index' for k in EK}}
    sim_names = {**vnames, 'equal': 'All six, equal weight', **{k: f"Hold {E[k]['index']}" for k in EK}}
    G = pd.DataFrame({k: (1 + rets[k].reindex(hix[:-1]).fillna(0)).cumprod().values for k in rets}, index=hix[1:])
    G = pd.concat([pd.DataFrame({k: [1.0] for k in rets}, index=[hix[0]]), G])
    seq = {'pick': picks, 'old': old, 'ret_nobuf': on_h(buffered(r52, 0.0)), 'ret_buf10': on_h(buffered(r52, 0.10)), 'riskadj_nobuf': nobuf,
           'ret26': on_h(buffered(r26.dropna(), OLD_BUFFER)), 'trend': old}
    sim_rows = []
    for k in rets:
        st_ = var_stats(seq[k].ffill().bfill() if k in seq else None, r=rets[k])
        if k not in seq: st_['switches_per_year'] = None
        st_['vol'] = round(float(rets[k].std() * math.sqrt(52) * 100), 1)
        sim_rows.append(dict(key=k, strategy=sim_names[k], group=groups[k], **st_))
    # consistency: the new series must agree with the summary files
    chk = {r['key']: r for r in out['ip_variants']}; bmap = {b['key']: b for b in bt}
    for r in sim_rows:
        ref = chk.get('riskadj' if r['key'] == 'pick' else r['key']) or bmap.get(r['key'])
        if ref and abs(ref['cagr'] - r['cagr']) > 0.1: raise RuntimeError(f"sim_strategies {r['key']} CAGR {r['cagr']} != summary {ref['cagr']}")
        n = len(rets[r['key']]); cg_ = (float(G[r['key']].iloc[-1]) ** (52.18 / n) - 1) * 100
        if abs(cg_ - r['cagr']) > 0.1: raise RuntimeError(f"sim_growth {r['key']} ends at {cg_:.2f}%/yr, table says {r['cagr']}")
    d3y = ((G['pick'] / G['pick'].shift(156)) ** (1 / 3) - (G['us'] / G['us'].shift(156)) ** (1 / 3)) * 100
    out['sim_strategies'] = sim_rows
    out['sim_growth'] = [dict(date=d, **{k: sg4(float(G.loc[d, k])) for k in rets}, pick_vs_us_3y=sg4(float(d3y.loc[d])) if pd.notna(d3y.loc[d]) else None) for d in G.index]
    out['sim_buying'] = [dict(date=pth[0], invested=round(pth[1]), invested_flat=round(mwpaths['flat_world'][i][1]), **{k: round(mwpaths[k][i][2]) for k in mwpaths}) for i, pth in enumerate(mwpaths['rule_pick'])]
    for r in mwrows:
        if abs(out['sim_buying'][-1][r['key']] - r['value']) > 1: raise RuntimeError(f"sim_buying {r['key']} != ip_buying")
    # ---- live record: the published weekly amounts into the published pick vs the same euros into the S&P 500 ETF
    COST_ = 0.002
    units, units_us, inv_, live = {k: 0.0 for k in EK}, 0.0, 0.0, []
    for h in [h for h in weekly_history if h['week'] >= LIVE_START]:
        ts = pd.Timestamp(h['week'])
        if ts not in W.index: continue
        px_ = W.loc[ts]; amt = float(h['amount'])
        units[h['pick']] += amt * (1 - COST_) / float(px_[h['pick']]); units_us += amt * (1 - COST_) / float(px_['us']); inv_ += amt
        plan_v = sum(u * float(px_[k]) for k, u in units.items()); us_v = units_us * float(px_['us'])
        live.append(dict(date=h['week'], pick=h['pick'], amount=amt, invested=round(inv_, 2), plan=round(plan_v, 2), sp500=round(us_v, 2),
                         plan_pct=round((plan_v / inv_ - 1) * 100, 2), sp500_pct=round((us_v / inv_ - 1) * 100, 2)))
    out['live_vs_sp500'] = live
    # ---- Free Money (Extra profit) live record vs the rule and the S&P 500, all as % of a one-off stake since LIVE_START.
    # Week i: the picks opened at Friday d_i close at d_(i+1); the rule holds the pick published at d_i; the S&P 500 holds SXR8.
    lw = [h for h in weekly_history if h['week'] >= LIVE_START and pd.Timestamp(h['week']) in W.index]
    ex_by = {}   # closed_on -> [pnl, stake] for both sides, long only, short only
    for l in extra_led:
        if l.get('leg') == 'Stocks' and l.get('closed_on'):
            e_ = ex_by.setdefault(l['closed_on'], {'both': [0.0, 0.0], 'Long': [0.0, 0.0], 'Short': [0.0, 0.0]})
            for k_ in ('both', l.get('side')):
                if k_ in e_: e_[k_][0] += float(l.get('pnl_eur') or 0); e_[k_][1] += float(l.get('euros') or 0)
    # all lines after 0.2% per trade: the weekly long/short closes and reopens every position (2 trades a week = 0.4%);
    # the rule and the S&P 500 pay 0.2% once when bought; the keepers pay 0.2% on each buy and sell (inside vstep)
    hA = {h['date']: h for h in (VA or {}).get('hist', [])}; hB = {h['date']: h for h in (VB or {}).get('hist', [])}
    fm, ce, cl, cs, cr, cu = [], 1.0, 1.0, 1.0, 1 - COST_, 1 - COST_
    if lw: fm.append(dict(date=lw[0]['week'], free_money=0.0, long_only=0.0, short_only=0.0, keep=hA.get(lw[0]['week'], {}).get('pct'), keep_trend=hB.get(lw[0]['week'], {}).get('pct'),
                          guard=hB.get(lw[0]['week'], {}).get('guard'), rule=round((cr - 1) * 100, 2), sp500=round((cu - 1) * 100, 2),
                          week_free_money=None, week_long_only=None, week_short_only=None, week_rule=None, week_sp500=None))
    for a_, b_ in zip(lw, lw[1:]):
        ta, tb = pd.Timestamp(a_['week']), pd.Timestamp(b_['week'])
        rr = float(W.loc[tb, a_['pick']]) / float(W.loc[ta, a_['pick']]) - 1; ru = float(W.loc[tb, 'us']) / float(W.loc[ta, 'us']) - 1
        e_ = ex_by.get(b_['week'], {}); wk_ = lambda k_: e_[k_][0] / e_[k_][1] if k_ in e_ and e_[k_][1] else None
        re_, rl_, rs_ = [None if v is None else v - 2 * COST_ for v in (wk_('both'), wk_('Long'), wk_('Short'))]
        if re_ is not None: ce *= 1 + re_
        if rl_ is not None: cl *= 1 + rl_
        if rs_ is not None: cs *= 1 + rs_
        cr *= 1 + rr; cu *= 1 + ru
        pc_ = lambda v: None if v is None else round(v * 100, 2)
        fm.append(dict(date=b_['week'], free_money=round((ce - 1) * 100, 2), long_only=round((cl - 1) * 100, 2), short_only=round((cs - 1) * 100, 2),
                       keep=hA.get(b_['week'], {}).get('pct'), keep_trend=hB.get(b_['week'], {}).get('pct'), guard=hB.get(b_['week'], {}).get('guard'), rule=round((cr - 1) * 100, 2), sp500=round((cu - 1) * 100, 2), week_free_money=pc_(re_), week_long_only=pc_(rl_), week_short_only=pc_(rs_),
                       week_rule=round(rr * 100, 2), week_sp500=round(ru * 100, 2)))
    out['free_money_live'] = fm

    # calendar years
    yrs = []
    for y in sorted({d[:4] for d in H.index}):
        m = [d for d in H.index[:-1] if d[:4] == y]
        if not m: continue
        r = {k: round((float((1 + series(k).loc[m].fillna(0)).prod()) - 1) * 100, 1) for k in ['pick'] + EK}
        top = picks.loc[m].value_counts()
        yrs.append(dict(year=y, held=E[top.index[0]]['index'], **r, pick_minus_us=round(r['pick'] - r['us'], 1), partial=len(m) < 50))
    out['ip_years'] = yrs
    # pick periods
    per, cur = [], None
    for d, k in picks.items():
        if cur and cur['key'] == k: cur['to'] = d; cur['weeks'] += 1
        else:
            cur = dict(key=k, index=E[k]['index'], frm=d, to=d, weeks=1); per.append(cur)
    for p in per:
        seg = [d for d in H.index[:-1] if p['frm'] <= d <= p['to']]
        p['ret'] = round((float((1 + R.loc[seg, p['key']].fillna(0)).prod()) - 1) * 100, 1) if seg else None
        wseg = round((float((1 + R.loc[seg, 'world'].fillna(0)).prod()) - 1) * 100, 1) if seg else None
        p['world_ret'] = wseg
    out['ip_periods'] = per[::-1]

    # ---- does the meter say anything? meter reading vs the MSCI World ETF over the next 4 and 52 weeks
    wv_ = H['world'].astype(float); m_ = H['meter'].astype(float)
    f4 = wv_.shift(-4) / wv_ - 1; f52 = wv_.shift(-52) / wv_ - 1
    mrows = []
    for lab, lo_, hi_ in [('Weak (−10 or lower)', -999, -10), ('Mixed (−10 to +15)', -10, 15), ('Strong (+15 to +40)', 15, 40), ('Very strong (+40 or higher)', 40, 999)]:
        sel = (m_ > lo_) & (m_ <= hi_) if lo_ > -999 else (m_ <= hi_)
        if hi_ == 999: sel = m_ > lo_
        mrows.append(dict(bucket=lab, weeks=int(sel.sum()), next_4w=round(float(f4[sel].mean()) * 100, 2) if f4[sel].notna().any() else None,
                          next_52w=round(float(f52[sel].mean()) * 100, 1) if f52[sel].notna().any() else None,
                          up_52w=round(float((f52[sel] > 0).mean()) * 100) if f52[sel].notna().any() else None))
    out['meter_test'] = mrows

    # ---- weekly_now / weekly_history / meter
    e = E[pick]
    reason = (f"{e['index']} has the best return for its risk: {row[pick] * 100:+.1f}% over 52 weeks at {vrow[pick] * 100:.0f}% volatility (score {srow[pick]:.2f})." if pick == leader else
              f"{E[leader]['index']} scores higher ({srow[leader]:.2f}), but not by more than {BUFFER} over {e['index']} ({srow[pick]:.2f}), so the pick stays.")
    if switched: reason = f"Switch: {E[prev_pick]['index']} → {e['index']}. " + reason
    out['weekly_now'] = [dict(week_of=week_of, decided_on=dstr, pick=pick, pick_index=e['index'], pick_etf=e['etf'], pick_fund=e['fund'], pick_isin=e['isin'],
                              pick_r52=round(float(row[pick]) * 100, 1), pick_score=round(float(srow[pick]), 2), pick_vol=round(float(vrow[pick]) * 100, 1), switched=switched, prev_pick=E[prev_pick]['index'] if prev_pick else None,
                              rule_change_from=E[RULE_CHANGE['from']]['index'] if dstr == RULE_CHANGE['week'] and pick != RULE_CHANGE['from'] else None,
                              leader=E[leader]['index'], pick_reason=reason, universe=uname, rank_method=method,
                              amount=amount, tier=tier,
                              reason=f"MSCI World {dd * 100:.1f}% from its record; {'above' if wv >= tr else 'below'} its 40-week line; VIX {v:.1f}; NFCI {nf:.2f}; Sahm {sa:.2f}.",
                              world_close=round(wv, 2), world_trend=round(tr, 2), world_ath=round(at, 2), from_ath_pct=round(dd * 100, 2),
                              vix=v, nfci=nf, sahm=sa, curve=cu, meter=meter, meter_label=label)]
    out['weekly_history'] = weekly_history
    out['meter_now'] = meter_rows
    summary = dict(week_of=week_of, date=dstr, pick=e['index'], etf=e['etf'], switched=switched, amount=amount, tier=tier, meter=meter, label=label,
                   positions=[(p['ticker'], f"{p['weight']}%", p['euros']) for p in positions],
                   demo_value=val_rows[-1]['value'], demo_bench=val_rows[-1]['benchmark'], demo_invested=val_rows[-1]['invested'],
                   trades=len([l for l in led if l['date'] == dstr and l['leg'] != 'Account']),
                   extra_week=round(sum(l['pnl_eur'] for l in extra_led if l['closed_on'] == dstr), 2), extra_total=round(sum(l['pnl_eur'] for l in extra_led), 2),
                   bt=next(b for b in bt if b['key'] == 'pick'))
    return out, summary
