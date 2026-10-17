# Backlog
Re-rank every run. Format: [priority] title — benefit / effort / notes. Move done items to CHANGELOG.md.

## Fixes and small wins
- [P1] Confirm the 06:17 UTC Saturday cron fires on 2026-10-24 (06:00 never fired; weekday 22:30 runs fire ~2 h late). If it doesn't, keep dispatching from this task and consider a second Saturday cron (e.g. 09:17) — reliability / small.
- [P1] S&P 500 member list (datasets/s-and-p-500-companies) is stale: it still lists PARA a year after the rename. Try Wikipedia's "List of S&P 500 companies" (keyless HTML; parse with pandas.read_html, needs lxml on the runner) as primary with the datasets CSV as fallback; compare symbol sets before switching — accuracy / medium.
- [P1] Page size: dashboard document 248 KB of 256 KiB. Unused CSS is only ~6 classes; the real wins are moving the AI-bot answer texts and the More pages' static prose to docs/data/*.json — reliability / medium.
- [P2] Yahoo's Friday closes for the .DE/.AS ETFs were missing at 09:48 UTC Saturday. Check the fallback log line ("ETF closes added from the per-ticker fallback") in next week's run summary; if hourly bars are used, compare them with the official close the following week — correctness / small.
- [P3] Demo page "Why this mix" table: show when each worst fall happened (e.g. −50% (2007–09)) and name the columns "Worst fall from peak" — clarity / small.
- [P2] Overview step 2: confirm the one-time rule-change note is gone (rule_change_from is null since 16 Oct) — small.
- [P3] sim_growth + sim_buying are ~300 KB together; if page load gets slow, thin them to every 2nd week before 2020 — speed / small.

## Watch (live record, no tuning)
- [R0b] Combinations suggest the demo's 30% stock share is low (best 40–90% with the guard). Re-check with the live record before proposing a demo change; needs owner approval.
- [R0] After ~26 live weeks compare Free Money current vs A vs B; if A or B leads and the 1991 stand-in agrees, propose switching (pull request).
- [R0d] Signal (0–1) = 0.5 timing + 0.5 own trend (untested part). After ~13 live weeks check whether it predicts next-week returns of the picks.
- [R0c] After ~13 live weeks: do higher stock scores or the 'very jumpy' flag predict next-week returns of the picks?

## Research questions (first Saturday of the month; log in EXPERIMENTS.csv before running)
- [R1] Monthly-only rebalance of the pick vs weekly with 0.25 buffer — fewer trades, maybe same return. (Next: 2026-11-07.)
- [R3] Stock score variants testable on French US data (12-1 vs 6-1 momentum, adding low volatility).
- [R4] Demo stock count: 3 vs 5 stocks (French decile data as proxy).
- [R2] Buffer sensitivity of the risk-adjusted rule (0.15 / 0.25 / 0.35) — robustness only, adopt nothing unless all data sets agree.
- [R5] Weekly amount tiers vs flat amount on 1927+ US data (2012–today: 13.2% vs 13.1% IRR, no real edge).
