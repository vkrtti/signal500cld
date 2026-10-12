"""Long-history research for IndexPilot (run weekly by GitHub Actions, or by hand).

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

ap = argparse.ArgumentParser(); ap.add_argument('--data', default='docs/data'); ap.add_argument('--offline'); ap.add_argument('--research', default='research_data')
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
            req = urllib.request.Request(BASE + fname, headers={'User-Agent': 'Mozilla/5.0 (IndexPilot research)'})
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

# ------------------------------------------------------------ momentum stocks: why the demo account holds what it holds
MOMD = None   # US momentum deciles (set by overlay), reused for the Free Money stand-in

def overlay():
    """US stocks sorted into 10 groups by 12-1 month momentum (value-weighted, monthly, Kenneth French data library).
    Compares the market with the demo's mix (70% market + 30% top-decile momentum stocks) and alternatives."""
    cache = os.path.join(args.research, 'mom_deciles.csv')
    if args.offline:
        if not os.path.exists(cache): return
        d = pd.read_csv(cache, dtype={'month': str}).set_index('month')
    else:
        m = monthly_block(fetch_zip_csv('10_Portfolios_Prior_12_2_CSV.zip'), ['Hi PRIOR', 'Lo PRIOR'])
        d = m.set_index('month')[['Hi PRIOR', 'Lo PRIOR']].rename(columns={'Hi PRIOR': 'hi', 'Lo PRIOR': 'lo'}) / 100
        d = d.join(f.set_index('month')[['mkt', 'rf']], how='inner')
        d.round(6).to_csv(cache)
    global MOMD; MOMD = d
    strat = {'market': ('100% US market', lambda x: x.mkt),
             'demo': ('Demo mix: 70% market + 30% top momentum stocks', lambda x: 0.7 * x.mkt + 0.3 * x.hi),
             'top': ('100% top momentum stocks', lambda x: x.hi),
             'ls': ('70% market + 15% long top / 15% short bottom', lambda x: 0.7 * x.mkt + 0.15 * x.hi - 0.15 * x.lo + 0.15 * x.rf)}
    rows = []
    for per, a, b in [('1927–today', '192601', '999999'), ('1990–today', '199001', '999999'), ('2000–2009', '200001', '200912'), ('2007–today', '200701', '999999'), ('2015–today', '201501', '999999')]:
        x = d[(d.index >= a) & (d.index <= b)]
        row = dict(period=per)
        for k, (nm, fn_) in strat.items():
            r = fn_(x); eq = (1 + r).cumprod(); n = len(r)
            row[k] = round((eq.iloc[-1] ** (12 / n) - 1) * 100, 1); row[k + '_dd'] = round(float((eq / eq.cummax() - 1).min()) * 100, 0)
        rows.append(row)
    save('hist_overlay', rows, 'Momentum stocks since 1927', 'Yearly return and worst fall of the US market, the demo account mix (70% market + 30% top-decile momentum stocks), all-momentum and a long/short version, by period (Kenneth French data library, before costs).')


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
    try: overlay()
    except Exception as e: log('WARN momentum overlay', e)

def rotation(df):
    """The weekly index pick tested on 35 years of regional data (monthly, US dollars).
    Current rule: each month hold the region with the best return per unit of risk (12-month return / 12-month volatility);
    a challenger must beat the current pick's score by more than 0.25. Also tests the previous rule (12-month return,
    5-point buffer) and other variants, with the results split into 1991-2008 and 2009-today."""
    regs = [k for k in ['US', 'Europe', 'Japan', 'AsiaPac', 'Emerging'] if k in df]
    d = df[regs + (['Developed'] if 'Developed' in df else [])].dropna()
    lvl = (1 + d).cumprod()
    r12 = lvl[regs] / lvl[regs].shift(12) - 1
    r6 = lvl[regs] / lvl[regs].shift(6) - 1
    sc = r12 / (d[regs].rolling(12).std() * np.sqrt(12))
    ma10 = lvl.rolling(10).mean()
    def path(score, buf, trend=False):
        held, out, picks = None, [], []
        for i in range(12, len(d) - 1):
            row = score.iloc[i]
            if row.isna().any(): continue
            lead = row.idxmax()
            if held is None or row[lead] - row[held] > buf: held = lead
            hold = held
            if trend and lvl[held].iloc[i] < ma10[held].iloc[i] and 'Developed' in d: hold = 'Developed'
            picks.append(held); out.append((d.index[i + 1], d[hold].iloc[i + 1]))
        return pd.Series([r for _, r in out], index=[t for t, _ in out]), picks
    def st(r, path_=None):
        eq = (1 + r).cumprod(); n = len(r)
        cg = lambda x: round((float((1 + x).prod()) ** (12 / len(x)) - 1) * 100, 1) if len(x) else None
        return dict(cagr=round((eq.iloc[-1] ** (12 / n) - 1) * 100, 1), max_dd=round(float((eq / eq.cummax() - 1).min()) * 100, 1),
                    vol=round(float(r.std() * np.sqrt(12) * 100), 1), sharpe=round(float(r.mean() / r.std() * np.sqrt(12)), 2),
                    switches_per_year=None if path_ is None else round(sum(1 for a, b in zip(path_, path_[1:]) if a != b) / (n / 12), 1),
                    first_half=cg(r[r.index < '200901']), second_half=cg(r[r.index >= '200901']), start=r.index[0], end=r.index[-1])
    variants = [('pick', 'Return per unit of risk, 0.25 buffer (current rule)', sc, 0.25, False), ('old', '12-month return, 5-point buffer (previous rule)', r12, 0.05, False),
                ('ret_nobuf', '12-month return, no buffer', r12, 0.0, False), ('ret26', '6-month return, 5-point buffer', r6, 0.05, False),
                ('ret_buf10', '12-month return, 10-point buffer', r12, 0.10, False), ('riskadj_nobuf', 'Return per unit of risk, no buffer', sc, 0.0, False),
                ('trend', '12-month return, 5-point buffer, developed world when below its 10-month line', r12, 0.05, True)]
    res = {}
    for k, nm, score, buf, tr in variants: res[k] = (nm,) + path(score, buf, tr)
    ix = res['pick'][1].index
    rows = []
    labels = {'US': 'Hold North America', 'Europe': 'Hold Europe', 'Japan': 'Hold Japan', 'AsiaPac': 'Hold Asia Pacific ex-Japan', 'Emerging': 'Hold Emerging markets', 'Developed': 'Hold Developed world'}
    rows.append(dict(key='pick', strategy='IndexPilot pick (return per unit of risk)', **st(res['pick'][1], res['pick'][2])))
    rows.append(dict(key='old', strategy='Previous rule (12-month return, 5-point buffer)', **st(res['old'][1], res['old'][2])))
    rows.append(dict(key='nobuf', strategy='Best score each month, no buffer', **st(res['riskadj_nobuf'][1], res['riskadj_nobuf'][2])))
    for k in regs + (['Developed'] if 'Developed' in d else []):
        rows.append(dict(key=k, strategy=labels[k], **st(d[k].loc[ix])))
    save('hist_rotation', rows, 'Index pick on 35 years of regional data', 'Monthly test of the index pick across North America, Europe, Japan, Asia Pacific ex-Japan and emerging markets (US dollars, Kenneth French data library).')
    save('hist_rotation_variants', [dict(key=k, rule=v[0], **{kk: vv for kk, vv in st(v[1], v[2]).items() if kk not in ('start', 'end', 'vol')}) for k, v in res.items()],
         'Index-pick variants on regional data', 'Each rule variant tested monthly 1991-today on regional data, with results for 1991-2008 and 2009-today.')
    dec = []
    for dd_, g in pd.Series(ix, index=ix).groupby(ix.str[:3]):
        m = list(g.index); k = 12 / len(m)
        cg = lambda r: round((float((1 + r.loc[m]).prod()) ** k - 1) * 100, 1)
        dec.append(dict(decade=dd_ + '0s', pick=cg(res['pick'][1]), nobuf=cg(res['old'][1]), world=cg(d['Developed']) if 'Developed' in d else None, us=cg(d['US'])))
    # rule vs North America (the S&P 500's region; French data, US dollars), month by month
    pr = res['pick'][1]; na = d['US'].loc[pr.index]
    gp, gu = (1 + pr).cumprod(), (1 + na).cumprod()
    roll = ((gp / gp.shift(36)) ** (1 / 3) - (gu / gu.shift(36)) ** (1 / 3)) * 100
    first = list(d.index).index(pr.index[0]) - 1
    reg = [dict(month=d.index[first], pick=1.0, us=1.0, diff_3y=None)] + [dict(month=m, pick=float(f'{gp[m]:.4g}'), us=float(f'{gu[m]:.4g}'),
           diff_3y=round(float(roll[m]), 2) if pd.notna(roll[m]) else None) for m in pr.index]
    cg_ = lambda g: (float(g.iloc[-1]) ** (12 / len(g)) - 1) * 100
    ref = next(r for r in rows if r['key'] == 'pick')['cagr']
    if abs(cg_(gp) - ref) > 0.1: raise RuntimeError(f'hist_regional pick {cg_(gp):.2f} != hist_rotation {ref}')
    # Free Money stand-in: the same idea on all US stocks (top 10% minus bottom 10% by 12-1 month momentum, half the money on
    # each side, no interest on cash, before costs and borrowing fees). Monthly; compared with the rule and North America.
    if MOMD is not None:
        md = MOMD.copy(); md['fm'] = (md['hi'] - md['lo']) / 2
        common = [m for m in pr.index if m in md.index]
        if len(common) > 120:
            fmr = md.loc[common, 'fm']; gf = (1 + fmr).cumprod(); gp2 = (1 + pr.loc[common]).cumprod(); gu2 = (1 + na.loc[common]).cumprod()
            start = d.index[list(d.index).index(common[0]) - 1]
            save('free_money_proxy', [dict(month=start, free_money=1.0, rule=1.0, us=1.0)] + [dict(month=m, free_money=float(f'{gf[m]:.4g}'), rule=float(f'{gp2[m]:.4g}'), us=float(f'{gu2[m]:.4g}')) for m in common],
                 'Free Money stand-in since 1991', 'Growth of 1: US momentum long/short (top 10% minus bottom 10% of US stocks, half the money each side, Kenneth French data) vs the index pick on regional data and North America. A stand-in, not the real picks.')
            def stat(key, nm, r, per):
                eq = (1 + r).cumprod(); yr = (1 + r).groupby(r.index.str[:4]).prod() - 1; full = yr[yr.index < r.index[-1][:4]]
                full = full[full.index > r.index[0][:4]] if r.index[0][4:] != '01' else full
                return dict(key=key, strategy=nm, period=per, cagr=round((float(eq.iloc[-1]) ** (12 / len(r)) - 1) * 100, 1), vol=round(float(r.std() * np.sqrt(12) * 100), 1),
                            max_dd=round(float((eq / eq.cummax() - 1).min()) * 100, 1), worst_year=round(float(full.min()) * 100, 1), worst_year_when=str(full.idxmin()),
                            best_year=round(float(full.max()) * 100, 1), pos_years=round(float((full > 0).mean()) * 100))
            allm = md['fm'].dropna(); per0 = allm.index[0][:4] + '–today'
            save('free_money_proxy_stats', [stat('fm_all', 'Free Money stand-in (US momentum long/short)', allm, per0), stat('mkt_all', 'US stock market', md['mkt'].loc[allm.index], per0),
                                            stat('fm', 'Free Money stand-in (US momentum long/short)', fmr, '1991–today'), stat('rule', 'IndexPilot rule (regions)', pr.loc[common], '1991–today'),
                                            stat('us', 'North America ≈ S&P 500', na.loc[common], '1991–today')],
                 'Free Money stand-in: statistics', 'Return per year, volatility, worst fall and worst year of the US momentum long/short stand-in, the US market, the index pick on regional data and North America (Kenneth French data, before costs).')
    save('hist_regional', reg, 'Index pick vs North America, monthly', 'Growth of 1 US dollar from 1991: the index pick on regional data vs North America (the S&P 500 region), with the rolling 3-year difference in points a year (Kenneth French data library).')
    yrs_ = []
    for y, g in pd.Series(pr.index, index=pr.index).groupby(pr.index.str[:4]):
        m = list(g.index); a = (float((1 + pr.loc[m]).prod()) - 1) * 100; b = (float((1 + na.loc[m]).prod()) - 1) * 100
        yrs_.append(dict(year=y, pick=round(a, 1), us=round(b, 1), pick_minus_us=round(a - b, 1), partial=len(m) < 12))
    save('hist_regional_years', yrs_, 'Index pick vs North America by year', 'Calendar-year return of the index pick on regional data and of North America, US dollars (Kenneth French data library).')
    save('hist_rotation_decades', dec, 'Index pick by decade', 'Yearly return by decade of the index pick, the previous rule, the developed world and North America.')


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
        df.round(6).to_csv(os.path.join(args.research, 'regions_monthly.csv'))
        rotation(df)
else:
    rp = os.path.join(args.research, 'regions_monthly.csv')
    if os.path.exists(rp): rotation(pd.read_csv(rp, dtype={'month': str}).set_index('month'))
log('done')
