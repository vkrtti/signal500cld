# Changelog (newest first)

## 2026-10-13
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
