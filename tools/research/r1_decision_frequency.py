"""Research R1 (EXPERIMENTS E015/E016): decide the index pick less often.
ETF 2012-today (weekly, euros): weekly decisions (current rule) vs decisions only on the last Friday of each month.
Regional 1991-today (monthly, US dollars): monthly decisions (current rule) vs decisions only in Mar/Jun/Sep/Dec.
Scores are computed at every close with data known then; between decision dates the pick is simply held.
Prints JSON; before costs, plus a line with 0.2% per switch (sell + buy ~ 2 x 0.1%)."""
import json, math, os, sys
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from indexpilot import weekly, scores, BUFFER

def hold_path(score, buf, decide):
    held, path = None, []
    for d, row in score.iterrows():
        if held is None or decide(d):
            lead = row.idxmax()
            if held is None or row[lead] - row[held] > buf: held = lead
        path.append(held)
    return pd.Series(path, index=score.index)

def stats(r, path, per_year, split, cost=0.0):
    sw = (path != path.shift(1)); sw.iloc[0] = False
    r = r - sw.reindex(r.index).fillna(False).astype(float) * cost
    eq = (1 + r).cumprod(); n = len(r)
    cg = lambda x: round((float((1 + x).prod()) ** (per_year / len(x)) - 1) * 100, 2)
    return dict(cagr=cg(r), sharpe=round(float(r.mean() / r.std() * math.sqrt(per_year)), 3),
                max_dd=round(float((eq / eq.cummax() - 1).min()) * 100, 1), switches_per_year=round(float(sw.sum()) / (n / per_year), 2),
                first_half=cg(r[r.index < split]), second_half=cg(r[r.index >= split]),
                sharpe_h1=round(float(r[r.index < split].mean() / r[r.index < split].std() * math.sqrt(per_year)), 3),
                sharpe_h2=round(float(r[r.index >= split].mean() / r[r.index >= split].std() * math.sqrt(per_year)), 3))

def etf():
    daily = pd.read_csv(os.path.join(ROOT, 'research_data/etf_daily.csv'), index_col=0, parse_dates=True)
    W = weekly(daily[daily.index >= '2011-01-01']).dropna()
    hist = pd.DataFrame(json.load(open(os.path.join(ROOT, 'docs/data/weekly_history.json'))))
    wk = pd.to_datetime(hist['week'] if 'week' in hist else hist['date'])
    r52, sc, vol = scores(W); sc = sc.dropna()
    R = W.pct_change().shift(-1)
    last_fri = set(sc.index.to_series().groupby(sc.index.to_period('M')).max())
    out = {}
    for key, decide in [('weekly', lambda d: True), ('monthly', lambda d: d in last_fri)]:
        p = hold_path(sc, BUFFER, decide)
        p = p[(p.index >= wk.min()) & (p.index <= wk.max())]
        r = pd.Series([R.loc[d, k] for d, k in p.items()], index=p.index).dropna()
        out[key] = {'before_costs': stats(r, p, 52.18, '2019-01-01'), 'switch_cost_0.2pct': stats(r, p, 52.18, '2019-01-01', 0.002)}
    return out

def regional():
    df = pd.read_csv(os.path.join(ROOT, 'research_data/regions_monthly.csv'), dtype={'month': str}).set_index('month')
    regs = ['US', 'Europe', 'Japan', 'AsiaPac', 'Emerging']
    d = df[regs].dropna(); lvl = (1 + d).cumprod()
    sc = (lvl / lvl.shift(12) - 1) / (d.rolling(12).std() * np.sqrt(12))
    sc = sc.iloc[12:len(d) - 1].dropna()
    nxt = d.shift(-1)
    out = {}
    for key, decide in [('monthly', lambda m: True), ('quarterly', lambda m: m[4:] in ('03', '06', '09', '12'))]:
        p = hold_path(sc, 0.25, decide)
        r = pd.Series([nxt.loc[m, k] for m, k in p.items()], index=[d.index[d.index.get_loc(m) + 1] for m in p.index])
        p.index = r.index
        out[key] = {'before_costs': stats(r, p, 12, '200901'), 'switch_cost_0.2pct': stats(r, p, 12, '200901', 0.002)}
    return out

if __name__ == '__main__':
    print(json.dumps({'etf': etf(), 'regional': regional()}, indent=1))
