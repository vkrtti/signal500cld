# Changelog (newest first)

## 2026-10-13
- Free Money: two long-only paper versions tracked live from 9 Oct (A Keepers, B Keepers + trend guard; state in free_money_variants_state.json, holdings in free_money_holdings.json), all live lines now after 0.2% per trade, stand-in adds long + trend guard (14.2%/yr since 1991). Tab rebuilt: 3 strategy cards, one live chart, one history chart, details folded away.
- Free Money: long-only and short-only lines in the live chart and the 1991 stand-in (stand-in: long 15.4%/yr, short −12.4%/yr, both 3.7%/yr; before costs). Index pick details: removed the growth chart and backtest tables that duplicated Simulation (page size).
- FAQ tab: 14 short answers from docs/data/faq.json with live numbers. Fixed direct links to the new tabs drawing nothing. Active tab stays visible on phones.
- Extra profit renamed "Free Money :D" (owner's request) and moved to the main tabs: live record vs the rule and the S&P 500 since 9 Oct, plus a stand-in simulation since 1991 (US momentum long/short: 3.7%/yr vs rule 9.8% and North America 11.0%; worst year −43.7% in 2009).
- Redesign for simplicity: Overview / Simulation / History / Method + More menu; live plan-vs-S&P 500 chart on the Overview; all strategies in one Simulation chart; History compares the rule with the S&P 500 (ETFs 2012–today, regions 1991–today). New data files listed in PLAYBOOK. Unfinished-week guard in the engine.
- Scheduled task "IndexPilot admin" created (Saturdays 12:47 Helsinki).
- Daily data update dispatched by hand: the 22:30 UTC scheduled run had not fired (no scheduled run has fired yet). Run succeeded; page test clean.
- PLAYBOOK: workflow dispatch must use the REST API (GraphQL is blocked).

## 2026-10-12
- Admin setup: admin/ memory folder, page/body.html as the page source, tools/build_site.py, tools/test/page_test.js, tools/shots.py.
- Overview explains once that the new rule replaced this week's earlier pick (MSCI Emerging Markets → MSCI World).

## 2026-10-11
- Index pick rule changed to return per unit of risk (52-week return ÷ volatility, 0.25 buffer); see EXPERIMENTS E002. Live from 2026-10-09.
- Signal meter renamed market meter; labels made descriptive because it has no predictive value (E008).
- Overview 3-step to-do; stale-data banner; rule-variant tables on the Index pick page; AI bot intents extended.
- Reliability: Sunday retry run, failed sources keep last data, weekly roll failure no longer breaks the job.
- Removed the remaining S&P 500 plan text and data files.
- Demo account: EUR 1,000 deposited weekly; 70% index ETF + 30% top 3 stocks; opened 2026-10-09.
