# Backlog
Re-rank every run. Format: [priority] title — benefit / effort / notes. Move done items to CHANGELOG.md.

## Fixes and small wins
- [P3] earnings_next.json is not in the 'IndexPilot weekly pick' task's download list, so only this admin run syncs it to the dashboard. Add it to that prompt if the owner wants it synced at 08:57 too — reliability / tiny.
- [P3] Check a weekly run log for 'FX fallback: TWD from FRED' only if Yahoo misses EURTWD=X; the code path is untested live (FRED blocked from this sandbox) — reliability / small.
- [P2] Page size: dashboard document 246.4 KB of 256 KiB (28 Nov moved index-pick and timing prose to method.json). Next candidates via data-mhtml: the 'Why US data?' template (~0.6 KB), the demo 'Why this mix' cards, the history intro paragraphs — reliability / small.
- [P2] Headline filter: the 28 Nov regex is keyword-based; next week skim news_feed for remaining personal-finance columns or quote pages, and check nothing real was dropped — quality / tiny.
- [P3] Hourly-bar fallback closes differed from Yahoo's official Friday close by ~0.1% (16 Oct EUNL 130.445 vs 130.54); the Sunday retry fixes the data. Consider deciding only on daily bars and letting Sunday retry instead — correctness / small.
- [P3] Demo page "Why this mix" table: show when each worst fall happened (e.g. −50% (2007–09)) and name the columns "Worst fall from peak" — clarity / small.
- [P3] sim_growth + sim_buying are ~300 KB together; if page load gets slow, thin them to every 2nd week before 2020 — speed / small.


## Watch (live record, no tuning)
- [R0e] Keepers A/B: −38.9% in 4 weeks (HPE, DELL, FTNT, then Recruit, APA, Targa all fell hard). 3-stock momentum is very concentrated; at the 26-week review, compare with the 1991 stand-in's worst 3-week spells before judging.
- [R0b] Combinations suggest the demo's 30% stock share is low (best 40–90% with the guard). Re-check with the live record before proposing a demo change; needs owner approval.
- [R0f] (earnings_next.json exists from 21 Nov; consider storing a results_week flag per extra_ledger/Keepers trade going forward so the 26-week review can count it.) Weekly long/short short side: AppLovin short lost 55.8% in its results week (4 Nov). Weakest-momentum shorts are exposed to earnings squeezes; at the 26-week review count how much of the short-side loss came from results weeks (no free earnings calendar yet).
- [R0] After ~26 live weeks compare Keepers (A, official since 19 Nov) vs B (guard) vs the previous long/short; if B leads and the 1991 stand-in agrees, propose B (pull request). Next strategy change: not before Q1 2027.
- [R0d] Signal (0–1) = 0.5 timing + 0.5 own trend (untested part). After ~13 live weeks check whether it predicts next-week returns of the picks.
- [R0c] After ~13 live weeks: do higher stock scores or the 'very jumpy' flag predict next-week returns of the picks?

## Research questions (first Saturday of the month; log in EXPERIMENTS.csv before running)
- [R3] (Next: 2026-12-05.) Stock score variants testable on French US data (12-1 vs 6-1 momentum, adding low volatility).
- [R4] Demo stock count: 3 vs 5 stocks (French decile data as proxy).
- [R2] Buffer sensitivity (note: R1 showed decision frequency barely matters once the buffer is there) of the risk-adjusted rule (0.15 / 0.25 / 0.35) — robustness only, adopt nothing unless all data sets agree.
- [R5] Weekly amount tiers vs flat amount on 1927+ US data (2012–today: 13.2% vs 13.1% IRR, no real edge).
