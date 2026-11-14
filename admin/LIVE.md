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
| 2026-11-06 | MSCI World (unchanged) | −1.83 | −1.83 | −2.10 | 4,634.69 | 5,000 | 4,904.72 |
| 2026-11-13 | MSCI World (unchanged) | +2.46 | +2.46 | +2.47 | 5,792.21 | 6,000 | 6,025.49 |

Weekly % are next-week returns of the euro ETFs, Friday close to Friday close, from research_data/etf_daily.csv (EUNL 131.64 → 130.54 → 129.84 → 129.685 → 127.315 → 130.45; SXR8 751.32 → 740.78 → 738.04 → 734.62 → 719.16 → 736.90). Each row's 1w % is the week that ENDED on that date (decided the Friday before).
Since live start (5 weeks of returns): pick (MSCI World) −0.90%, S&P 500 ETF −1.92%; pick vs MSCI World 0.0 points (the pick has been MSCI World every week), +1.02 points vs the S&P 500 ETF.

## Plan vs benchmarks (live_vs_sp500: weekly amount into the pick, 0.2% per buy)
- Put in €360 → plan €360.81 (+0.22%), S&P 500 ETF €359.39 (−0.17%): plan +€1.42.

## Demo (EUR 1,000 a week)
- €5,792.21 vs €6,000 deposited vs €6,025.49 in MSCI World: −€233.28 (was −€270.03). EUNL core +0.5%; Petrobras sold this week (fell to rank 209, −22.8%); bought Nippon Express (rank 1), added to Viatris (+5.2%) and TSMC (−1.3%).

## Free Money (% of a one-off stake since 9 Oct, after 0.2% per trade)
| Line | Since 9 Oct | Last week |
|---|---|---|
| Weekly long/short (current) | −14.87% (long −25.42%, short −5.38%) | +2.17% |
| Keepers (A) | −33.39% | about +8.9% |
| Keepers + trend guard (B) | −33.39% (guard off, same as A) | about +8.9% |
| The rule (index pick) | −1.10% | +2.46% |
| S&P 500 | −2.12% | +2.47% |
Week to 13 Nov: A and B kept Recruit, APA, Targa (since 30 Oct −8.5/−8.3/−5.6%). This week's long/short: long Nippon Express, Humana, Viatris; short Aptiv, Coinbase, Boston Scientific. Five weeks: noise, no conclusions.

## Alert rule
If the pick trails MSCI World by more than 5 points over 26 live weeks, put it first in the report and investigate.
