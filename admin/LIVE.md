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

Weekly % are next-week returns of the euro ETFs, Friday close to Friday close, from research_data/etf_daily.csv (EUNL 131.64 → 130.54 → 129.84 → 129.685 → 127.315; SXR8 751.32 → 740.78 → 738.04 → 734.62 → 719.16). The 6 Nov closes were revised by the 10:55 UTC rerun (EUNL 127.24 → 127.315, SXR8 718.60 → 719.16). Each row's 1w % is the week that ENDED on that date (decided the Friday before).
Since live start (4 weeks of returns): pick (MSCI World) −3.29%, S&P 500 ETF −4.28%; pick vs MSCI World 0.0 points (the pick has been MSCI World every week), +0.99 points vs the S&P 500 ETF.

## Plan vs benchmarks (live_vs_sp500: weekly amount into the pick, 0.2% per buy)
- Put in €300 → plan €293.69 (−2.10%), S&P 500 ETF €292.30 (−2.57%): plan +€1.39.

## Demo (EUR 1,000 a week)
- €4,634.69 vs €5,000 deposited vs €4,904.72 in MSCI World: −€270.03 (was −€126.09). The stock leg (30%) is the drag: MediaTek sold on its 25% trailing stop (−22.3%, −€56.51), Petrobras −22.1%, TSMC −12.2%; the EUNL core is −1.8%. Viatris bought this week.

## Free Money (% of a one-off stake since 9 Oct, after 0.2% per trade)
| Line | Since 9 Oct | Last week |
|---|---|---|
| Weekly long/short (current) | −16.68% (long −27.38%, short −6.90%) | −14.82% |
| Keepers (A) | −38.85% | about −14.7% |
| Keepers + trend guard (B) | −38.85% (guard off, same as A) | about −14.7% |
| The rule (index pick) | −3.48% | −1.83% |
| S&P 500 | −4.47% | −2.10% |
Week to 6 Nov: longs Recruit −11.5%, APA −15.5%, Targa −16.0%; the short in AppLovin lost 55.8% (228.50 → 356.10 USD; news confirms a jump of 20%+ on its 4 Nov results), BSX −1.8%, COIN +4.7%. A and B hold the same three longs (Keep). Four weeks: noise, no conclusions, but the 3-stock concentration risk noted in BACKLOG R0e is visible.

## Alert rule
If the pick trails MSCI World by more than 5 points over 26 live weeks, put it first in the report and investigate.
