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
| 2026-11-20 | MSCI World (unchanged) | −5.73 | −5.73 | −5.59 | 6,413.82 | 7,000 | 6,679.83 |

Weekly % are next-week returns of the euro ETFs, Friday close to Friday close, from research_data/etf_daily.csv (EUNL 131.64 → 130.54 → 129.84 → 129.685 → 127.315 → 130.44 → 122.965; SXR8 751.32 → 740.78 → 738.04 → 734.62 → 719.16 → 736.84 → 695.62; Yahoo revised 13 Nov by −0.01). Each row's 1w % is the week that ENDED on that date (decided the Friday before).
Since live start (6 weeks of returns): pick (MSCI World) −6.59%, S&P 500 ETF −7.41%; pick vs MSCI World 0.0 points (the pick has been MSCI World every week), +0.82 points vs the S&P 500 ETF.

## Plan vs benchmarks (live_vs_sp500: weekly amount into the pick, 0.2% per buy)
- Put in €460 → plan €439.91 (−4.37%), S&P 500 ETF €439.06 (−4.55%): plan +€0.85.

## Demo (EUR 1,000 a week)
- €6,413.82 vs €7,000 deposited vs €6,679.83 in MSCI World: −€266.01 (was −€233.28). No sales; bought EUNL, TSMC, Viatris, Nippon Express with the new €1,000.

## Free Money (% of a one-off stake since 9 Oct, after 0.2% per trade)
| Line | Since 9 Oct | Last week |
|---|---|---|
| Keepers (A, official since 19 Nov) | −37.41% | about −6.0% |
| Keepers + trend guard (B) | −37.41% (guard off, same as A) | about −6.0% |
| Weekly long/short (previous; official until 19 Nov) | −14.32% (long −31.63%, short +3.72%) | +0.64% (long −8.34%, short +9.62%) |
| The rule (index pick) | −6.78% | −5.73% |
| S&P 500 | −7.60% | −5.59% |
Week to 20 Nov (sell-off week): A and B kept Recruit, APA, Targa (since 30 Oct −12.3/−14.7/−11.6%). This week's long/short: long Target, BayCurrent, Takeda; short Skydance, Aptiv, Naspers. Six weeks: noise, no conclusions.

## Alert rule
If the pick trails MSCI World by more than 5 points over 26 live weeks, put it first in the report and investigate.
