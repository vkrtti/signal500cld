# Changelog (newest first)

## 2026-10-31
- Weekly roll: neither Saturday cron had fired by 10:48 UTC (the 09:47 one fired at 11:04 last week); dispatched by hand, succeeded, decided on Friday 30 Oct (pick MSCI World unchanged, €60, meter +39). Friday closes present, no NaN.
- Workflow: the Friday 22:30 UTC cron always fires ~01:45 UTC Saturday (after Friday's close), so a scheduled run on a Saturday/Sunday (UTC) now does the weekly roll. The roll should exist before the 07:57 UTC "IndexPilot weekly pick" task; a missing Friday close still stops the roll and a later run retries.
- FX: ECB euro reference rates (keyless) as fallback when a Yahoo exchange rate is missing (Method and PLAYBOOK updated).
- Page: the research sub-tab header + "Why US data?" note was repeated on three pages; now one template cloned at load (−1.6 KB on the 256 KiB dashboard document).
- Checked: markets.json S&P 500 dated the latest session (30 Oct); stock universe has only current S&P 500 members (NU, PDD are from the emerging-market list).
- Dashboard: synced every data file changed since the weekly-pick task's 09:00 UTC sync (it ran before the roll again) plus the page.

## 2026-10-24
- Weekly roll: the Saturday 06:17 UTC scheduled run had not fired by 09:48 UTC; dispatched by hand, succeeded, decided on Friday 23 Oct (pick MSCI World unchanged, €60). Added a second Saturday cron at 09:47 UTC.
- S&P 500 member list: the stock universe now comes from the current constituents file; the fundamentals file (which still listed PARA, WBD, HES, ANSS, K and ~40 other former members, and missed ~44 new ones such as APP, HOOD, DDOG) is only used for current members. Tested on today's files: 503 members, 457 with fundamentals, no PARA/WBD.
- Markets: FRED's SP500 lagged (last value 21 Oct on 24 Oct); update.py now tops it up with Yahoo ^GSPC closes for finished sessions after FRED's last date (keyless). Method data table updated.
- Checked: the one-time rule-change note is gone from the Overview (rule_change_from null).
- Dashboard: synced the 25 data files changed since each dataset's last sync (the 07:57 UTC weekly-pick task had synced before the roll).

## 2026-10-17
- Weekly roll: the Saturday 06:00 UTC scheduled run never fired; dispatched by hand. Yahoo's bulk download returned an empty Friday row for all six euro ETFs, so the first roll decided on Thursday's close and the demo wrote NaN (cash, benchmark, IEMA sale). Fixes: empty rows dropped, per-ticker fallback (daily, then hourly bars) for missing latest sessions, the Saturday roll stops (Sunday retry) if Friday is still missing, NaN-safe demo prices, and the data writer never writes NaN (null + warning).
- Demo files (demo_state, demo_ledger, demo_value) restored to the last good version (9 Oct, committed by the bot at 00:42 UTC) to undo the NaN write, then the week was rerun on Friday's close. No valid row changed. Demo reruns on the same day now restart from a saved 'prev' state (tested: second rerun left the ledger identical).
- Stock ranking skips stale/reused tickers (USD price under 1 or −95% in a year). PARA (Paramount became PSKY in 2025; Yahoo still quotes PARA at 0.54) had been shorted 9–16 Oct (+18%, stays in extra_ledger); this week's short is BSX instead.
- Demo core switched from MSCI Emerging Markets (IEMA, −5.6%) to MSCI World at this roll as the rule says; demo_value rows gain core_etf.
- Workflow: weekly crons at 06:17 UTC (off the hour), runner pinned to ubuntu-24.04 (ubuntu-latest moves to 26 on 19 Oct), checkout v5 / setup-python v6.
- Live charts with few weeks tick on data dates (were hourly ticks); last x label no longer clipped. 'Extra profit' renamed Free Money :D everywhere left (bot answers, Method, dataset titles).
- Checked: Free Money A −19.53% matches a hand calculation from the holdings; Overview and Free Money live charts draw from week 2.

## 2026-10-14
- Signal 0–1 on every stock: half market timing (research.py timing(): expanding-window model 1937–today, no look-ahead; 0–0.2 band: +13.4% avg next year, 29% losing years; 0.8–1: +22.7%, 15%), half own trend. Timing card on Free Money, timing line in Your plan. First reading 0.03 (end Aug 2026).
- Stock lists (Your plan, Overview, Free Money) show each stock's rank as 'stronger than X%' (shorts: 'weaker than X%') plus 'very jumpy' (volatility > 60%) and 'trend guard on' tags; FAQ entry explains them.

## 2026-10-13
- Three main tabs (Overview, Your plan, FAQ), the rest under More. New 'Your plan' page: buy amount + ISIN + when, what to sell (nothing unless the list says so), optional Keepers stocks with Buy/Keep/Sell, next check date. Method text moved to docs/data/method.json (page −21 KB). free_money_holdings gains an action field.
- Simulation: Combinations section (the index pick + 0–100% in a stock strategy, 1991–today, both halves): best return per risk was the rule + 70% Keepers with guard (13.3%/yr, worst year −18.1%, Sharpe 0.72 vs 0.48 for the rule alone), but the best share differs by half (90% vs 40%). Live 70/30 mixes shown from 16 Oct. Page slimmed (dead code, shorter AI guide); tools/dash_page.py also minifies CSS.
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
