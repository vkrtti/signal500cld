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
| 2026-11-13 | MSCI World (unchanged) | +2.45 | +2.45 | +2.46 | 5,791.95 | 6,000 | 6,025.11 |
| 2026-11-20 | MSCI World (unchanged) | −5.92 | −5.92 | −5.81 | 6,413.82 | 7,000 | 6,679.83 |
| 2026-11-27 | MSCI World (unchanged) | +3.50 | +3.50 | +3.44 | 7,634.96 | 8,000 | 7,899.57 |

Weekly % are next-week returns of the euro ETFs, Friday close to Friday close, from research_data/etf_daily.csv (EUNL 131.64 → 130.54 → 129.84 → 129.685 → 127.315 → 130.44 → 122.715 → 127.01; SXR8 751.32 → 740.78 → 738.04 → 734.62 → 719.16 → 736.84 → 694.06 → 717.94; Yahoo revised 20 Nov EUNL 122.965 → 122.715 and SXR8 695.62 → 694.06 after the early roll). Each row's 1w % is the week that ENDED on that date.
Since live start (7 weeks of returns): pick (MSCI World) −3.52%, S&P 500 ETF −4.44%; pick vs MSCI World 0.0 points (the pick has been MSCI World every week), +0.92 points vs the S&P 500 ETF.

## Plan vs benchmarks (live_vs_sp500: weekly amount into the pick, 0.2% per buy)
- Put in €620 → plan €617.76 (−0.36%), S&P 500 ETF €616.49 (−0.57%): plan +€1.27. (20 Nov amount was €200, meter +2; 27 Nov €60, meter +29.)

## Demo (EUR 1,000 a week)
- €7,634.96 vs €8,000 deposited vs €7,899.57 in MSCI World: −€264.61 (was −€266.01).

## Free Money (% of a one-off stake since 9 Oct, after 0.2% per trade)
| Line | Since 9 Oct | Last week |
|---|---|---|
| Keepers (A, official since 19 Nov) | −36.88% | about +0.8% |
| Keepers + trend guard (B) | −36.88% (guard off, same as A) | about +0.8% |
| Weekly long/short (previous; official until 19 Nov) | −13.45% (long −28.40%, short +0.94%) | +1.02% (long +4.73%, short −2.69%) |
| The rule (index pick) | −3.71% | +3.50% |
| S&P 500 | −4.63% | +3.44% |
Week to 27 Nov: A and B still hold Recruit, APA, Targa (since 30 Oct −13.0/−12.7/−10.9%). This week's long/short: long BayCurrent, Takeda, Target; short Coinbase, Insulet, Skydance. Seven weeks: noise, no conclusions.

## Alert rule
If the pick trails MSCI World by more than 5 points over 26 live weeks, put it first in the report and investigate.
