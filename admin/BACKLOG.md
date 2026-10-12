# Backlog
Re-rank every run. Format: [priority] title — benefit / effort / notes. Move done items to CHANGELOG.md.

## Fixes and small wins
- [P2] Free Money live chart: check it draws after the 16 Oct close and that its weekly % matches extra_weeks (same ledger, same formula) — correctness / small.
- [P1] Confirm GitHub scheduled runs fire (none had by 2026-10-12 23:10 UTC; a manual daily run was dispatched then). If still none by 2026-10-17, add a fallback (e.g. the Saturday admin task dispatches the weekly roll itself) and tell the owner — reliability / small.
- [P1] Demo: switch the core from MSCI Emerging Markets (IEMA) to the pick at the next roll and check the trades in demo_ledger are sensible — correctness / small / first roll under the new rule.
- [P1] demo_value.pick records the current pick, not what the core holds (currently says world while holding IEMA) — add a `core` field or label it clearly — correctness / small.
- [P3] Demo page "Why this mix" table: show when each worst fall happened (e.g. −50% (2007–09)) and name the columns "Worst fall from peak" — clarity / small / user asked why all are red.
- [P2] Overview step 2: remove the one-time rule-change note after week 2026-10-12 (RULE_CHANGE in indexpilot.py only fires for that week; check it is gone).
- [P2] Overview live chart: check it starts drawing after the 2nd live week (2026-10-16) and the numbers match live_vs_sp500 — correctness / small.
- [P3] sim_growth + sim_buying are ~300 KB together; if page load gets slow, thin them to every 2nd week before 2020 — speed / small.

## Research questions (one per month, log in EXPERIMENTS.csv before running)
- [R1] Monthly-only rebalance of the pick vs weekly with 0.25 buffer — fewer trades, maybe same return.
- [R2] Buffer sensitivity of the risk-adjusted rule (0.15 / 0.25 / 0.35) — only to confirm robustness, NOT to pick the best; adopt nothing unless all data sets agree.
- [R3] Stock score variants that can be tested on French US data (12-1 vs 6-1 momentum, adding low volatility).
- [R4] Demo stock count: 3 vs 5 stocks (French decile data as proxy).
- [R5] Weekly amount tiers: does buying more in deep drawdowns beat a flat amount on 1927+ US data? (Current evidence: weekly rule 13.2% vs flat 13.1% IRR on World 2012–today — no real edge.)
