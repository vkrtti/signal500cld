"""Weekly update for the S&P 500 Buy Signals dashboard.

Usage:
  python3 weekly_update.py STATE_DIR INPUTS_JSON FUNDAMENTALS_CSV CONSTITUENTS_CSV OUT_DIR

STATE_DIR holds the current dataset files: weekly_now.json, weekly_history.json,
demo_positions.json, demo_ledger.json (the last two may be missing on the first run).
INPUTS_JSON: {"date": "YYYY-MM-DD" (last close), "spx": close, "vix": .., "nfci": .., "sahm": .., "t10y3m": ..}
Writes to OUT_DIR: weekly_now, weekly_history, meter_now, rank_top, rank_bottom,
demo_positions, demo_ledger (all .json). Safe to re-run for the same date.
"""
import json, os, sys, datetime as dt
import pandas as pd, numpy as np

state, inp_path, fin, cons, out = sys.argv[1:6]
os.makedirs(out, exist_ok=True)
L = lambda n, d=None: json.load(open(os.path.join(state, n))) if os.path.exists(os.path.join(state, n)) else d
inp = json.load(open(inp_path))
date, spx, vix, nfci, sahm, curve = inp['date'], float(inp['spx']), float(inp['vix']), float(inp['nfci']), float(inp['sahm']), float(inp['t10y3m'])
prev = L('weekly_now.json')[0]
hist = L('weekly_history.json')
positions = L('demo_positions.json', [])
ledger = L('demo_ledger.json', [])
week_of = (dt.date.fromisoformat(date) + dt.timedelta(days=(7 - dt.date.fromisoformat(date).weekday()) % 7 or 7)).isoformat()

# ---------- trend, record high, weekly amount ----------
past = [h for h in hist if h['week'] != date]
trend = float(np.mean([h['close'] for h in past[-39:]] + [spx]))
ath = max(float(prev['ath']), spx)
dd = spx / ath - 1
if vix < 30 and spx < trend and (sahm >= 0.5 or nfci > 0): amount, tier = 40, 'Stress'
elif vix >= 30 or dd <= -0.20: amount, tier = 200, 'Bear market or panic'
elif dd <= -0.10: amount, tier = 150, 'Correction'
elif dd <= -0.05: amount, tier = 100, 'Dip'
else: amount, tier = 60, 'Normal'

# ---------- signal-strength meter (-100 strong sell ... +100 strong buy) ----------
clip = lambda x, a, b: max(a, min(b, x))
comp = [
    ('Trend', 0.25, clip((spx / trend - 1) / 0.05, -1, 1), f'{(spx / trend - 1) * 100:+.1f}% vs trend line'),
    ('Discount from record', 0.20, clip(-dd / 0.15, 0, 1), f'{dd * 100:.1f}% from record'),
    ('Fear (VIX)', 0.15, 1 if vix >= 30 else 0.5 if vix >= 20 else -0.5 if vix < 13 else 0, f'VIX {vix:.1f}'),
    ('Credit conditions (NFCI)', 0.15, -1 if nfci > 0 else -0.3 if nfci > -0.3 else 0.3, f'NFCI {nfci:.2f}'),
    ('Recession risk (Sahm)', 0.15, -1 if sahm >= 0.5 else -0.5 if sahm >= 0.3 else 0.3, f'Sahm {sahm:.2f}'),
    ('Yield curve', 0.10, -0.5 if curve < 0 else 0.2, f'10Y−3M {curve:+.2f}'),
]
meter = round(100 * sum(w * s for _, w, s, _ in comp))
label = 'Strong buy' if meter >= 40 else 'Buy' if meter >= 15 else 'Neutral' if meter > -10 else 'Sell' if meter > -25 else 'Strong sell'
meter_rows = [dict(component=c, weight=round(w * 100), score=round(s, 2), contribution=round(100 * w * s, 1), reading=t) for c, w, s, t in comp]
meter_rows.append(dict(component='Total', weight=100, score=None, contribution=meter, reading=label))

# ---------- rank all S&P 500 members ----------
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
def note(x):
    if pd.notna(x.pe) and x.pe < 6: return 'P/E unusually low: verify'
    if pd.isna(x.pe): return 'Loss-making'
    return ''
rows = [dict(rank=int(x['rank']), ticker=x.Symbol, company=x.Name, sector=x.sector, score=round(x.score, 1),
             value=round(x.value * 100), momentum=round(x.mom * 100), pe=None if pd.isna(x.pe) else round(x.pe, 1),
             off_52w_high=round(x.off_high * 100, 1), price=round(x.Price, 2), note=note(x)) for _, x in f.iterrows()]
price = {r['ticker']: r['price'] for r in rows}
top, bottom = rows[:50], rows[-50:][::-1]

# ---------- demo account: close last week's positions, open this week's ----------
if not (positions and positions[0]['entry_date'] == date):
    for p in positions:
        exitp = spx if p['ticker'] == 'S&P 500' else price.get(p['ticker'])
        n = ''
        if exitp is None: exitp, n = p['entry_price'], 'No price (left index?): closed flat'
        sgn = 1 if p['side'] == 'Long' else -1
        ret = sgn * (exitp / p['entry_price'] - 1)
        ledger.append(dict(id=f"{p['week_of']}-{p['ticker']}", week_of=p['week_of'], closed_on=date, leg=p['leg'], ticker=p['ticker'],
                           side=p['side'], euros=p['euros'], entry_price=p['entry_price'], exit_price=round(exitp, 2),
                           return_pct=round(ret * 100, 2), pnl_eur=round(p['euros'] * ret, 2), note=n))
    positions = []
    spx_eur = 0 if abs(meter) < 10 else round(500 * abs(meter) / 100)
    if spx_eur:
        positions.append(dict(id=f'{week_of}-S&P 500', week_of=week_of, entry_date=date, leg='Index', ticker='S&P 500', company='S&P 500 index',
                              side='Long' if meter > 0 else 'Short', euros=spx_eur, entry_price=spx, reason=f'Meter {meter:+d} ({label})'))
    longs = [r for r in top if not r['note']][:3]
    shorts = [r for r in bottom if 'verify' not in r['note']][:3]
    for r, side in [(r, 'Long') for r in longs] + [(r, 'Short') for r in shorts]:
        positions.append(dict(id=f"{week_of}-{r['ticker']}", week_of=week_of, entry_date=date, leg='Stocks', ticker=r['ticker'], company=r['company'],
                              side=side, euros=83.33, entry_price=r['price'], reason=f"Rank {r['rank']} of {len(rows)} (score {r['score']})"))

# ---------- weekly history ----------
hist = past + [dict(week=date, close=round(spx), amount=amount, meter=meter)]
now = [dict(week_of=week_of, decided_on=date, amount=amount, tier=tier,
            reason=f'S&P 500 {spx:,.0f} is {dd * 100:.1f}% from its record {ath:,.0f}; VIX {vix:.1f}; price {"above" if spx >= trend else "below"} its trend line ({trend:,.0f}); NFCI {nfci:.2f}; Sahm {sahm:.2f}.',
            spx_close=spx, ath=ath, from_ath_pct=round(dd * 100, 2), vix=vix, ma200=round(trend, 2), nfci=nfci, sahm=sahm,
            meter=meter, meter_label=label)]

W = lambda n, d: json.dump(d, open(os.path.join(out, n), 'w'), separators=(',', ':'))
W('weekly_now.json', now); W('weekly_history.json', hist); W('meter_now.json', meter_rows)
W('rank_top.json', top); W('rank_bottom.json', bottom)
W('demo_positions.json', positions); W('demo_ledger.json', ledger)
print(json.dumps(dict(date=date, week_of=week_of, amount=amount, tier=tier, meter=meter, label=label,
                      positions=[(p['ticker'], p['side'], p['euros']) for p in positions],
                      closed=len([l for l in ledger if l['closed_on'] == date]),
                      week_pnl=round(sum(l['pnl_eur'] for l in ledger if l['closed_on'] == date), 2),
                      total_pnl=round(sum(l['pnl_eur'] for l in ledger), 2))))
