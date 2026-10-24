# Backlog
Re-rank every run. Format: [priority] title — benefit / effort / notes. Move done items to CHANGELOG.md.

## Fixes and small wins
- [P1] Saturday crons: 06:17 had not fired by 10:30 UTC on 2026-10-24; a 09:47 cron was added. Next run: list runs and check which Saturday crons fired (and when); keep dispatching if none did — reliability / small.
- [P1] Check next roll's log for "S&P 500: N members, M with fundamentals" (should be ~503 / ~457) and that no stock outside the current list appears in pick_rank — correctness / small.
- [P1] The "IndexPilot weekly pick" task (Saturday 07:57 UTC) ran before this week's roll existed (roll dispatched 09:48 UTC), so its message used last week's data. Proposed to the owner: move it to ~13:00 Helsinki or have it dispatch the roll when weekly_now.decided_on is not the latest Friday — needs owner / small.
- [P2] markets.json: check next week that spx is dated the latest session (Yahoo ^GSPC top-up added 2026-10-24 for the FRED lag) — correctness / small.
- [P1] Page size: dashboard document 248 KB of 256 KiB. Unused CSS is only ~6 classes; the real wins are moving the AI-bot answer texts and the More pages' static prose to docs/data/*.json — reliability / medium.
- [P3] Hourly-bar fallback closes differed from Yahoo's official Friday close by ~0.1% (16 Oct EUNL 130.445 vs 130.54); the Sunday retry fixes the data. Consider deciding only on daily bars and letting Sunday retry instead — correctness / small.
- [P3] Demo page "Why this mix" table: show when each worst fall happened (e.g. −50% (2007–09)) and name the columns "Worst fall from peak" — clarity / small.
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
