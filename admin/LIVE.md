---
Live record since the first live decision (2026-10-09). Never use these numbers to tune rules.
Update every weekly run from docs/data (weekly_history, live_vs_sp500, demo_value, free_money_live).
---
# Live record

| Week decided | Pick | Pick 1w % | MSCI World 1w % | S&P 500 ETF 1w % | Demo value € | Deposited € | Same deposits in World € |
|---|---|---|---|---|---|---|---|
| 2026-10-09 | MSCI World (new rule; old rule had published MSCI Emerging Markets) | — | — | — | 993.15 | 1,000 | 1,000 |
| 2026-10-16 | MSCI World (unchanged) | −0.91 | −0.91 | −1.49 | 1,940.08 | 2,000 | 1,990.92 |

Weekly % are next-week returns of the euro ETFs, Friday close to Friday close (EUNL 131.64 → 130.445, SXR8 751.32 → 740.16).

## Plan vs benchmarks (live_vs_sp500: weekly amount into the pick, 0.2% per buy)
- Put in €120 → plan €119.22 (−0.65%), S&P 500 ETF €118.87 (−0.94%): plan +€0.35.
- Pick vs MSCI World since live start: 0.0 points (the pick has been MSCI World every week).

## Demo (EUR 1,000 a week)
- €1,940.08 vs €2,000 deposited vs €1,990.92 in MSCI World: −€50.84. Most of it is the IEMA core bought on 9 Oct under the old rule (−5.6%, sold 16 Oct) and trading costs.

## Free Money (% of a one-off stake since 9 Oct, after 0.2% per trade)
| Line | Since 9 Oct |
|---|---|
| Weekly long/short (current) | −4.61% (long side −19.77%, short side +10.55%) |
| Keepers (A) | −19.53% |
| Keepers + trend guard (B) | −19.53% (guard off, so same as A) |
| The rule (index pick) | −1.11% |
| S&P 500 | −1.68% |
One week of data: noise. Note the 9–16 Oct short side included PARA (stale ticker, fixed 17 Oct; its +18% is in the ledger and stays).

## Alert rule
If the pick trails MSCI World by more than 5 points over 26 live weeks, put it first in the report and investigate.
