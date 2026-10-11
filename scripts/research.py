"""Long-history research for Signal500 (run weekly by GitHub Actions, or by hand).

Downloads Kenneth French's data library (US market, value, momentum, risk-free rate since 1926;
regional markets since 1990) and recomputes:
  hist_plans.json      10/20/30% plans 1927-today (1x hold, 2x/3x with the 10-month trend rule, and without)
  hist_plans_growth.json  growth of 1 unit, year-end values
  hist_weekly_rule.json   weekly EUR 40-200 rule vs a flat amount, money-weighted returns by start year
  hist_factors.json    value, momentum and the 50/50 long/short mix: long-run statistics
  hist_decades.json    returns by decade for the market, plans and factors
  hist_factor_growth.json  growth of the factor mix, year-end values
  regions.json / regions_years.json  regional stock markets since 1990

Usage: python scripts/research.py [--data docs/data] [--offline research_data]
Offline mode reads research_data/ff_us_monthly.csv (columns month,mkt_rf,hml,rf,mom in %) and keeps regions as they are.
A failed download keeps the previous files.
"""
import argparse, datetime as dt, io, json, os, sys, time, urllib.request, zipfile
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument('--data', default='docs/data'); ap.add_argument('--offline')
args = ap.parse_args(); D = args.data
NOW = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
BASE = 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/'
log = lambda *a: print('[research]', *a, flush=True)

def save(name, obj, title=None, desc=None):
    json.dump(obj, open(os.path.join(D, name + '.json'), 'w'), separators=(',', ':'))
    mp = os.path.join(D, 'meta.json'); meta = json.load(open(mp)) if os.path.exists(mp) else {}
    m = meta.setdefault(name, {'title': title or name, 'description': desc or '', 'refresh': 'weekly'})
    if title: m['title'] = title
    if desc: m['description'] = desc
    m['updated'] = NOW
    json.dump(meta, open(mp, 'w'), indent=1); log('saved', name)

def fetch_zip_csv(fname):
    for attempt in range(4):
        try:
            req = urllib.request.Request(BASE + fname, headers={'User-Agent': 'Mozilla/5.0 (Signal500 research)'})
            raw = urllib.request.urlopen(req, timeout=90).read()
            z = zipfile.ZipFile(io.BytesIO(raw)); return z.read(z.namelist()[0]).decode('latin-1')
        except Exception as e:
            log(f'fetch failed {fname} ({attempt + 1}/4): {e}'); time.sleep(5 * (attempt + 1))
    raise RuntimeError('could not fetch ' + fname)

def monthly_block(txt, cols):
    """First block of YYYYMM rows of a French CSV -> DataFrame with the requested columns (in %)."""
    lines = txt.splitlines(); hdr = None; rows = []
    for ln in lines:
        p = [x.strip() for x in ln.split(',')]
        if hdr is None and len(p) > 1 and p[0] == '' and any(c in p for c in cols): hdr = p; continue
        if hdr is not None:
            if len(p[0]) == 6 and p[0].isdigit(): rows.append(p)
            elif rows: break
    df = pd.DataFrame(rows, columns=['month'] + hdr[1:])
    return df[['month'] + cols].assign(**{c: pd.to_numeric(df[c]) for c in cols})

# ------------------------------------------------------------ load data
if args.offline:
    f = pd.read_csv(os.path.join(args.offline, 'ff_us_monthly.csv'), dtype={'month': str})
else:
    try:
        f3 = monthly_block(fetch_zip_csv('F-F_Research_Data_Factors_CSV.zip'), ['Mkt-RF', 'HML', 'RF'])
        mo = monthly_block(fetch_zip_csv('F-F_Momentum_Factor_CSV.zip'), ['Mom'])
        f = f3.merge(mo, on='month').rename(columns={'Mkt-RF': 'mkt_rf', 'HML': 'hml', 'RF': 'rf', 'Mom': 'mom'})
        os.makedirs('research_data', exist_ok=True); f.to_csv('research_data/ff_us_monthly.csv', index=False)
    except Exception as e:
        log('ERROR French US data unavailable, keeping previous research files:', e); f = None

if f is not None:
    f['date'] = pd.to_datetime(f.month, format='%Y%m')
    for c in ['mkt_rf', 'hml', 'rf', 'mom']: f[c] = f[c] / 100
    f = f.sort_values('date').reset_index(drop=True)
    f['mkt'] = f.mkt_rf + f.rf
    f['vm'] = 0.5 * f.hml + 0.5 * f.mom
    f['lvl'] = (1 + f.mkt).cumprod(); f['ma10'] = f.lvl.rolling(10).mean()
    f['dd'] = f.lvl / f.lvl.cummax() - 1
    f['var_m'] = np.maximum(f.mkt ** 2, (f.mkt ** 2).rolling(3).mean().fillna(f.mkt ** 2))
    f['year'] = f.date.dt.year
    first, last = f.month.iloc[0], f.month.iloc[-1]
    period = f'{first[:4]}–{last[:4]}'
    last_label = pd.Timestamp(f.date.iloc[-1]).strftime('%b %Y')
    fee = {1: 0.0007, 2: 0.006, 3: 0.0075}

    def plan(L, trend):
        out = []
        for i in range(len(f)):
            on = (not trend) or (i > 0 and f.lvl[i - 1] > f.ma10[i - 1])
            out.append(f.rf[i] if not on else max(L * f.mkt[i] - (L - 1) * f.rf[i] - (L * L - L) / 2 * f.var_m[i] - fee[L] / 12, -1.0))
        return np.array(out)

    def stats(r, target=None):
        eq = np.cumprod(1 + r); n = len(r) / 12
        ann = pd.Series(r).groupby(f.year.values).apply(lambda x: (1 + x).prod() - 1)
        full = ann[(ann.index > f.year.iloc[0]) & (ann.index < f.year.iloc[-1])] if len(ann) > 2 else ann
        with np.errstate(all='ignore'):
            r10 = (eq[120:] / eq[:-120]) ** (1 / 10) - 1
        r10 = r10[np.isfinite(r10)]
        s = dict(cagr=round((max(eq[-1], 0) ** (1 / n) - 1) * 100, 1), max_dd=round((eq / np.maximum.accumulate(eq) - 1).min() * 100, 1),
                 worst_year=round(full.min() * 100, 1), worst_year_when=int(full.idxmin()), best_year=round(full.max() * 100, 1),
                 pos_years=round((full > 0).mean() * 100), median_10y=round(float(np.median(r10)) * 100, 1) if len(r10) else None,
                 min_10y=round(float(r10.min()) * 100, 1) if len(r10) else None, max_10y=round(float(r10.max()) * 100, 1) if len(r10) else None,
                 growth=round(float(eq[-1]), 2))
        if target: s['hit_target_10y_pct'] = round(float((r10 >= target).mean()) * 100) if len(r10) else 0
        since90 = f.date >= '1990-01-01'
        s['since_1990'] = round(((1 + r[since90.values]).prod() ** (12 / since90.sum()) - 1) * 100, 1)
        return s, eq

    defs = [('10%', 'Steady', '1x index, buy and hold', 1, False, .10), ('20%', 'Growth', '2x, 10-month trend rule', 2, True, .20),
            ('30%', 'Aggressive', '3x, 10-month trend rule', 3, True, .30), ('2x-no-rule', '2x, no rule', '2x held all the time', 2, False, None),
            ('3x-no-rule', '3x, no rule', '3x held all the time', 3, False, None)]
    rows, curves = [], {}
    for key, name, desc, L, t, tg in defs:
        s, eq = stats(plan(L, t), tg); s.update(plan=key, name=name, setup=desc, period=period); rows.append(s); curves[key] = eq
    save('hist_plans', rows, 'Plans over 100 years', f'The 10/20/30% plans simulated {period} on Kenneth French US market total returns (monthly), with daily-reset drag, fees and cash at the T-bill rate.')
    ye = f.date.dt.month.eq(12) | (f.index == len(f) - 1)
    save('hist_plans_growth', [dict(year=int(f.year[i]) if f.date[i].month == 12 else int(f.year[i]) + 0, p10=round(float(curves['10%'][i]), 4), p20=round(float(curves['20%'][i]), 4),
                                    p30=round(float(curves['30%'][i]), 4), x2=round(float(curves['2x-no-rule'][i]), 6), x3=round(float(curves['3x-no-rule'][i]), 8))
                               for i in np.where(ye)[0]], 'Plan growth since 1927', 'Value of 1 unit invested in Jan 1927, at each year end.')

    # weekly amount rule vs flat amount (drawdown tiers; VIX/NFCI/Sahm do not exist before 1990)
    amt = np.array([200 if d <= -0.2 else 150 if d <= -0.1 else 100 if d <= -0.05 else 60 for d in f.dd.shift(1).fillna(0)], float)
    def irr(fl, r):
        v = 0
        for c, x in zip(fl, r): v = (v + c) * (1 + x)
        lo, hi = -0.05, 0.05; n = len(fl)
        for _ in range(100):
            m = (lo + hi) / 2; val = sum(-c * (1 + m) ** (n - i) for i, c in enumerate(fl)) + v
            lo, hi = (m, hi) if val > 0 else (lo, m)
        return ((1 + m) ** 12 - 1) * 100
    wr = []
    for lab, start in [(f'{first[:4]}–today', first), ('From the 1929 peak', '192909'), ('From 1966 (1970s inflation)', '196601'), ('From 1990', '199001'), ('From 2000', '200001')]:
        msk = (f.month >= start).values; a = amt[msk]; r = f.mkt.values[msk]
        wr.append(dict(period=lab, rule=round(irr(a, r), 2), flat=round(irr(np.full(len(a), a.mean()), r), 2), avg_weekly=round(float(a.mean())), crash_share=round(float((a >= 150).mean()) * 100)))
    for w in wr: w['diff'] = round(w['rule'] - w['flat'], 2)
    save('hist_weekly_rule', wr, 'Weekly rule over 100 years', 'Money-weighted yearly return of the EUR 40-200 drawdown tiers vs a flat amount, US market total returns (French).')

    # factors
    fr = []
    for key, name in [('hml', 'Value (cheap minus expensive)'), ('mom', 'Momentum (winners minus losers)'), ('vm', 'Value + momentum 50/50')]:
        r = f[key].values; eq = np.cumprod(1 + r); dd = eq / np.maximum.accumulate(eq) - 1
        ann = pd.Series(r).groupby(f.year.values).apply(lambda x: (1 + x).prod() - 1); ann = ann[ann.index < f.year.iloc[-1]]
        r10 = (eq[120:] / eq[:-120]) ** (1 / 10) - 1
        uw = mx = 0; end_mx = None
        for i in range(len(eq)):
            uw = uw + 1 if dd[i] < 0 else 0
            if uw > mx: mx, end_mx = uw, f.month[i]
        s07 = (f.date >= '2007-01-01').values
        fr.append(dict(factor=name, key=key, premium=round((eq[-1] ** (1 / (len(r) / 12)) - 1) * 100, 1), vol=round(r.std() * np.sqrt(12) * 100, 1),
                       max_dd=round(dd.min() * 100, 1), worst_year=round(ann.min() * 100, 1), worst_year_when=int(ann.idxmin()), pos_years=round((ann > 0).mean() * 100),
                       pos_10y=round((r10 > 0).mean() * 100), longest_underwater_years=round(mx / 12, 1), since_2007=round(((1 + r[s07]).prod() ** (12 / s07.sum()) - 1) * 100, 1),
                       last_12m=round(((1 + r[-12:]).prod() - 1) * 100, 1), period=period))
    save('hist_factors', fr, 'Value and momentum since 1927', f'Long/short factor returns {period} (Kenneth French data library), premium over cash, before costs.')
    vmeq = np.cumprod(1 + f.vm.values)
    save('hist_factor_growth', [dict(year=int(f.year[i]), vm=round(float(vmeq[i]), 4), hml=round(float(np.cumprod(1 + f.hml.values)[i]), 4), mom=round(float(np.cumprod(1 + f.mom.values)[i]), 4)) for i in np.where(ye)[0]],
         'Factor growth since 1927', 'Value of 1 unit in each long/short factor, year-end.')

    # decades
    p1, p2, p3 = plan(1, False), plan(2, True), plan(3, True)
    dec = []
    for d, g in f.groupby(f.year // 10 * 10):
        idx = g.index.values; k = 12 / len(idx)
        cg = lambda x: round(((1 + x).prod() ** k - 1) * 100, 1)
        dec.append(dict(decade=f'{d}s', market=cg(p1[idx]), plan20=cg(p2[idx]), plan30=cg(p3[idx]), value=cg(g.hml.values), momentum=cg(g.mom.values), mix=cg(g.vm.values), cash=cg(g.rf.values)))
    save('hist_decades', dec, 'Returns by decade', f'Yearly returns by decade {period}: US market, 20%/30% plans, value, momentum, their mix and cash.')
    log('US research done through', last_label)

# ------------------------------------------------------------ regional markets
if not args.offline:
    files = {'US': ('North_America_3_Factors_CSV.zip', 'North America'), 'Developed': ('Developed_3_Factors_CSV.zip', 'Developed world'),
             'DevExUS': ('Developed_ex_US_3_Factors_CSV.zip', 'Developed ex-US'), 'Europe': ('Europe_3_Factors_CSV.zip', 'Europe'),
             'Japan': ('Japan_3_Factors_CSV.zip', 'Japan'), 'AsiaPac': ('Asia_Pacific_ex_Japan_3_Factors_CSV.zip', 'Asia Pacific ex-Japan'),
             'Emerging': ('Emerging_5_Factors_CSV.zip', 'Emerging markets')}
    series = {}
    for k, (fn, nm) in files.items():
        try:
            d = monthly_block(fetch_zip_csv(fn), ['Mkt-RF', 'RF']); d['r'] = (d['Mkt-RF'] + d['RF']) / 100; series[k] = d.set_index('month').r
        except Exception as e: log('WARN region', k, e)
    if len(series) >= 3:
        df = pd.DataFrame(series).dropna(how='all'); df = df[df.index >= '199007']
        stats_rows, years = [], {}
        for k, (fn, nm) in files.items():
            if k not in df: continue
            r = df[k].dropna(); eq = (1 + r).cumprod(); n = len(r)
            yr = (1 + r).groupby(r.index.str[:4]).prod() - 1
            for y, v in yr.items(): years.setdefault(y, {'year': y})[k] = round(v * 100, 1)
            full = yr[(yr.index > '1990') & (yr.index < r.index[-1][:4])]
            stats_rows.append(dict(key=k, region=nm, cagr=round((eq.iloc[-1] ** (12 / n) - 1) * 100, 1), vol=round(r.std() * np.sqrt(12) * 100, 1),
                                   max_dd=round((eq / eq.cummax() - 1).min() * 100, 1), worst_year=round(full.min() * 100, 1), worst_year_when=full.idxmin(),
                                   last10=round(((1 + r.iloc[-120:]).prod() ** (1 / 10) - 1) * 100, 1), ytd=round(yr.iloc[-1] * 100, 1),
                                   corr_us=round(float(r.corr(df['US'])), 2) if 'US' in df else None, through=r.index[-1]))
        save('regions', stats_rows, 'World stock markets since 1990', 'Total returns in US dollars by region, Jul 1990 to the latest month (Kenneth French data library).')
        save('regions_years', list(years.values()), 'World markets by year', 'Calendar-year total returns by region in US dollars.')
log('done')
