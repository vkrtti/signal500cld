---
Live record since the first live decision (2026-10-09). Never use these numbers to tune rules.
Update every weekly run from docs/data (weekly_history, live_vs_sp500, demo_value, free_money_live).
---
# Live record

| Week decided | Pick | Pick 1w % | MSCI World 1w % | S&P 500 ETF 1w % | Demo value € | Deposited € | Same deposits in World € |
|---|---|---|---|---|---|---|---|
| 2026-10-09 | MSCI World (new rule; old rule had published MSCI Emerging Markets) | — | — | — | 993.15 | 1,000 | 1,000 |
| 2026-10-16 | MSCI World (unchanged) | −0.84 | −0.84 | −1.40 | 1,941.29 | 2,000 | 1,991.64 |
| 2026-10-23 | MSCI World (unchanged) | −0.54 | −0.54 | −0.37 | 2,924.38 | 3,000 | 2,980.96 |
| 2026-10-30 | MSCI World (unchanged) | −0.12 | −0.12 | −0.46 | 3,851.32 | 4,000 | 3,977.41 |

Weekly % are next-week returns of the euro ETFs, Friday close to Friday close, from research_data/etf_daily.csv (EUNL 131.64 → 130.54 → 129.84 → 129.685; SXR8 751.32 → 740.78 → 738.04 → 734.62). The 16 Oct closes were revised by the Sunday 18 Oct rerun (EUNL 130.445 → 130.54, SXR8 740.16 → 740.78: the Saturday run had used the hourly-bar fallback), so week-1 numbers differ slightly from last week's table.
Since live start (3 weeks of returns): pick (MSCI World) −1.49%, S&P 500 ETF −2.22%; pick vs MSCI World 0.0 points (the pick has been MSCI World every week), +0.73 points vs the S&P 500 ETF.

## Plan vs benchmarks (live_vs_sp500: weekly amount into the pick, 0.2% per buy)
- Put in €240 → plan €238.17 (−0.76%), S&P 500 ETF €237.41 (−1.08%): plan +€0.76.

## Demo (EUR 1,000 a week)
- €3,851.32 vs €4,000 deposited vs €3,977.41 in MSCI World: −€126.09 (was −€56.53). The stock leg (30%) is the drag: Petrobras −10.9%, MediaTek −8.3%, TSMC −2.5% on their buys; the EUNL core is −0.4%. Plus the 9 Oct IEMA loss and costs.

## Free Money (% of a one-off stake since 9 Oct, after 0.2% per trade)
| Line | Since 9 Oct | Last week |
|---|---|---|
| Weekly long/short (current) | −2.18% (long −14.45%, short +8.91%) | +1.06% |
| Keepers (A) | −28.29% | about −14% |
| Keepers + trend guard (B) | −28.29% (guard off, same as A) | about −14% |
| The rule (index pick) | −1.68% | −0.12% |
| S&P 500 | −2.42% | −0.46% |
A and B sold HPE, DELL and FTNT at the 30 Oct close (out of the top 20% and/or 25% stop) and bought Recruit (6098.T), APA and Targa (TRGP). Their first three stocks lost ~28% in three weeks: the risk of 3-stock momentum. Sale prices could not be checked against a second quote from this sandbox (Yahoo/stooq blocked); news confirms HPE and Dell fell sharply in October. Three weeks: noise, no conclusions.

## Alert rule
If the pick trails MSCI World by more than 5 points over 26 live weeks, put it first in the report and investigate.
