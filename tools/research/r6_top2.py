"""Research E017: hold the two best indexes 50/50 instead of one.
ETF 2012-today (weekly, euros) and regional 1991-today (monthly, US dollars). Current rule (E002) for comparison.
Top-2 rule: start with the two highest scores; at each decision, the best non-held index replaces the weaker held one
only if its score beats that holding's score by more than the buffer (0.25). Returns: 50/50, rebalanced at each decision.
Scores use data known at each close; the next period's return is earned. Prints JSON (before costs and with 0.2% per switch of half the money)."""
import json, math, os, sys
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from indexpilot import weekly, scores, BUFFER

def one(score, buf):
    held, out = None, []
    for d, row in score.iterrows():
        lead = row.idxmax()
        if held is None or row[lead] - row[held] > buf: held = lead
        out.append((held,))
    return pd.Series(out, index=score.index)

def two(score, buf):
    held, out = None, []
    for d, row in score.iterrows():
        if held is None: held = tuple(row.sort_values(ascending=False).index[:2])
        else:
            weak = min(held, key=lambda k: row[k]); rest = row.drop(list(held)); ch = rest.idxmax()
            if row[ch] - row[weak] > buf: held = tuple(k for k in held if k != weak) + (ch,)
        out.append(tuple(sorted(held)))
    return pd.Series(out, index=score.index)

def stats(r, path, per_year, split, cost=0.0):
    sw = pd.Series([0.0] + [len(set(a) - set(b)) / len(a) for a, b in zip(path.values[1:], path.values[:-1])], index=path.index)
    r = r - sw.reindex(r.index).fillna(0) * cost
    eq = (1 + r).cumprod(); n = len(r)
    cg = lambda x: round((float((1 + x).prod()) ** (per_year / len(x)) - 1) * 100, 2)
    sh = lambda x: round(float(x.mean() / x.std() * math.sqrt(per_year)), 3)
    a, b = r[r.index < split], r[r.index >= split]
    return dict(cagr=cg(r), sharpe=sh(r), max_dd=round(float((eq / eq.cummax() - 1).min()) * 100, 1), switches_per_year=round(float(sw.sum()) / (n / per_year), 2),
                h1=cg(a), h2=cg(b), sharpe_h1=sh(a), sharpe_h2=sh(b))

def run(sc, nxt, per_year, split, index_of_next):
    out = {}
    for key, fn in [('current_E002', one), ('top2_E017', two)]:
        p = fn(sc, BUFFER)
        r = pd.Series([np.mean([nxt.loc[d, k] for k in ks]) for d, ks in p.items()], index=[index_of_next(d) for d in p.index]).dropna()
        p.index = [index_of_next(d) for d in p.index]; p = p.loc[r.index]
        out[key] = {'before_costs': stats(r, p, per_year, split), 'cost_0.2pct': stats(r, p, per_year, split, 0.002)}
    return out

def etf():
    daily = pd.read_csv(os.path.join(ROOT, 'research_data/etf_daily.csv'), index_col=0, parse_dates=True)
    W = weekly(daily[daily.index >= '2011-01-01']).dropna()
    r52, sc, vol = scores(W); sc = sc.dropna(); sc = sc[sc.index < W.index[-1]]
    R = W.pct_change().shift(-1)
    return run(sc, R, 52.18, pd.Timestamp('2019-01-01'), lambda d: d)

def regional():
    df = pd.read_csv(os.path.join(ROOT, 'research_data/regions_monthly.csv'), dtype={'month': str}).set_index('month')
    regs = ['US', 'Europe', 'Japan', 'AsiaPac', 'Emerging']
    d = df[regs].dropna(); lvl = (1 + d).cumprod()
    sc = (lvl / lvl.shift(12) - 1) / (d.rolling(12).std() * np.sqrt(12))
    sc = sc.iloc[12:len(d) - 1].dropna()
    nxt = d.shift(-1); pos = {m: i for i, m in enumerate(d.index)}
    return run(sc, nxt, 12, '200901', lambda m: d.index[pos[m] + 1])

if __name__ == '__main__':
    print(json.dumps({'etf': etf(), 'regional': regional()}, indent=1))
