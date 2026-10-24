---
Live record since the first live decision (2026-10-09). Never use these numbers to tune rules.
Update every weekly run from docs/data (weekly_history, live_vs_sp500, demo_value, free_money_live).
---
# Live record

| Week decided | Pick | Pick 1w % | MSCI World 1w % | S&P 500 ETF 1w % | Demo value € | Deposited € | Same deposits in World € |
|---|---|---|---|---|---|---|---|
| 2026-10-09 | MSCI World (new rule; old rule had published MSCI Emerging Markets) | — | — | — | 993.15 | 1,000 | 1,000 |
| 2026-10-16 | MSCI World (unchanged) | −0.84 | −0.84 | −1.40 | 1,941.29 | 2,000 | 1,991.64 |
| 2026-10-23 | MSCI World (unchanged) | −0.54 | −0.54 | −0.37 | 2,924.43 | 3,000 | 2,980.96 |

Weekly % are next-week returns of the euro ETFs, Friday close to Friday close, from research_data/etf_daily.csv (EUNL 131.64 → 130.54 → 129.84; SXR8 751.32 → 740.78 → 738.04). The 16 Oct closes were revised by the Sunday 18 Oct rerun (EUNL 130.445 → 130.54, SXR8 740.16 → 740.78: the Saturday run had used the hourly-bar fallback), so week-1 numbers differ slightly from last week's table.
Since live start: pick (MSCI World) −1.37%, S&P 500 ETF −1.77%; pick vs MSCI World 0.0 points (the pick has been MSCI World every week).

## Plan vs benchmarks (live_vs_sp500: weekly amount into the pick, 0.2% per buy)
- Put in €180 → plan €178.50 (−0.83%), S&P 500 ETF €178.36 (−0.91%): plan +€0.14.

## Demo (EUR 1,000 a week)
- €2,924.43 vs €3,000 deposited vs €2,980.96 in MSCI World: −€56.53. Mostly the IEMA core bought on 9 Oct under the old rule (−5.6%) plus trading costs; this week the stock leg moved about −0.5%, like World.

## Free Money (% of a one-off stake since 9 Oct, after 0.2% per trade)
| Line | Since 9 Oct | Last week |
|---|---|---|
| Weekly long/short (current) | −3.21% (long −16.31%, short +9.02%) | +1.47% |
| Keepers (A) | −16.26% | |
| Keepers + trend guard (B) | −16.26% (guard off, same as A) | |
| The rule (index pick) | −1.56% | −0.54% |
| S&P 500 | −1.96% | −0.37% |
Two weeks of data: noise. A and B still hold the 9 Oct buys HPE (−22.8%), DELL (−22.1%), FTNT (−7.6%).

## Alert rule
If the pick trails MSCI World by more than 5 points over 26 live weeks, put it first in the report and investigate.
