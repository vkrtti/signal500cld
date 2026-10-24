# IndexPilot admin playbook
Your memory between runs. Keep under two pages; merge or delete outdated lines.

## Map
- Page source: page/body.html (one file: CSS + HTML + JS). It runs in two places:
  1. Site: `python3 tools/build_site.py` wraps it into docs/index.html (head with assets/theme.css, d3 7.9.0 from cdnjs, assets/runtime.js; footer). Never edit docs/index.html by hand.
  2. Dashboard: https://claude.ai/artifact/FDxHtYoKRx211m4hmtTptM, document files/index.html = {"text": <page/body.html>}.
- Page layout (since 2026-10-13, owner's choice): only three main tabs: Overview (`home`), Your plan (`plan`: the beginner's step-by-step for this week, built from weekly_now + free_money_holdings strategy A) and FAQ (`faq`, text in docs/data/faq.json). Everything else is under More: Simulation (`sim`, incl. Combinations), History (`longrun`), Free Money :D (`extra`), Method (`strategy`, text in docs/data/method.json, injected once), stocks, demo, indexes, week, news, markets, research. SX.MAIN lists the main tabs; old #/tab links still work.
- New data (weekly): sim_strategies, sim_growth, sim_buying, live_vs_sp500 (indexpilot.py, with built-in consistency checks against ip_variants/ip_backtest/ip_buying that raise on a mismatch) and hist_regional, hist_regional_years (research.py, checked against hist_rotation). Free Money: free_money_live (indexpilot.py, weekly % since LIVE_START for Free Money, the rule and the S&P 500) and free_money_variants_state (never delete: the paper A/B portfolios; a same-day rerun restarts from its 'prev'), free_money_holdings, free_money_proxy / free_money_proxy_stats (research.py: US momentum top-minus-bottom decile, half each side, a labelled stand-in because the real picks can't be backtested). Colours: rule = accent, S&P 500 = --sp token, on every chart.
- Page API: `dash.data(name)`, `dash.calc(...)`, `dash.onData(...)`, `dash.setLink('#/'+tab)`. docs/assets/runtime.js lists DATASETS; a new data file must be added there, in docs/data/meta.json, and as a new dashboard dataset doc.
- Pipeline (.github/workflows/update.yml): weekdays 22:30 UTC (update.py + news.py); Saturday 06:17 and 09:47 UTC weekly roll (also indexpilot.py, research.py), Sunday 06:17 UTC retry (runner pinned to ubuntu-24.04); manual (GraphQL is blocked, so `gh workflow run` fails; use REST): `gh api -X POST repos/vkrtti/signal500cld/actions/workflows/update.yml/dispatches -f ref=main -f 'inputs[weekly]=true'` (or false for the daily update). List runs: `gh api 'repos/vkrtti/signal500cld/actions/workflows/update.yml/runs?per_page=10' -q '.workflow_runs[]|[.event,.conclusion,.created_at]|@tsv'`. Run logs: read `::notice::`/`::error::` annotations via `gh api repos/vkrtti/signal500cld/check-runs/<job_id>/annotations`.
- scripts/indexpilot.py: pick (score = 52-week return ÷ 52-week volatility, BUFFER 0.25, LIVE_START 2026-10-09), amount tiers, market meter, stock ranking, Extra profit, demo account, backtests. scripts/research.py: Kenneth French history tests. scripts/update.py: FRED gauges, markets (FRED SP500 topped up with Yahoo ^GSPC closes when FRED lags), S&P 500 lists. Stock universe: members from datasets/s-and-p-500-companies constituents.csv (current); fundamentals from datasets/s-and-p-500-companies-financials (lags index changes by months, so it is inner-joined to the current members). scripts/news.py: RSS titles and links only.
- History files you must never delete or rewrite: docs/data/weekly_history.json (published rows from LIVE_START), demo_state, demo_ledger, extra_ledger, free_money_variants_state, docs/data/archive/.

## Data duty (owner's request, 2026-10-13)
- Every run: refresh all data (dispatch the weekly roll and/or a daily run when stale), fix failing sources, and sync every changed data file to the dashboard, not only the ones you touched.
- Look for free, public, keyless data that makes the site more accurate (prices, longer history, fundamentals, index members, FX); add it when it clearly helps and document the source in Method and here.

## Verify before every push
1. `(cd tools/test && npm ci)` once per run, then `node tools/test/page_test.js` → must print NO ERRORS (exit 0). EMPTY visuals for ip-strip (drawn with <i>, not svg), ex-chart and demo-chart (fewer than 2 weeks of data, empty-state text shows) are expected.
2. `python3 tools/build_site.py && python3 tools/shots.py shots` → NO PROBLEMS; open a few PNGs and look.
3. Python: `python3 -m py_compile scripts/*.py`. For pipeline changes dispatch a real weekly run (REST command above) and check it commits sensible data.

## Dashboard sync
- Upload a changed data file: Artifact publish (url above, asset: true, file_path; one file per call) → returns /_blob/<id>.
- Then one ArtifactData batch: update datasets/<name> with source {kind:"file", url:"/_blob/<id>", name:"<name>.json"}, updated {at, by:"Claude"}, if_version from a fresh `list` of collection datasets.
- Page: `python3 tools/dash_page.py /tmp/page_doc.json` (light minify; the dashboard caps one document at 256 KiB), then set files/index.html from that file with if_version. Check its output with page_test.js (`--html` writes the minified page).
- The Saturday 10:57 Helsinki task "IndexPilot weekly pick" syncs datasets and messages the user; if you change a data file name or format, update its prompt (scheduled task trig_01Qxph4Y6DKzJdtsojazZdV3) and say so in the report.

## Lessons
- Keep long static text (FAQ, Method) in docs/data/*.json, not page/body.html: the dashboard copy is capped at 256 KiB per document.
- New tabs must draw even when data arrived before their script ran (direct links like #/faq): the last page script calls SX.draw() once after wiring.
- A weekly run before Friday's close used to decide on an unfinished week (pandas W-FRI bins label the coming Friday). indexpilot.py now drops that week unless offline; mid-week manual weekly runs are safe.
- Scheduled runs: weekday 22:30 UTC runs fire (~2.5 h late); Saturday weekly crons did NOT fire on 2026-10-17 (06:00) or by 10:30 UTC on 2026-10-24 (06:17); the Sunday retry fired 5 h late. A 09:47 Saturday cron was added 2026-10-24. Every run: list runs, and if no weekly roll since Friday, dispatch inputs[weekly]=true. Job logs can't be downloaded from here (blob host blocked): read annotations and the commit diff instead.
- Weekly reruns are safe (same-day reruns of the demo and Free Money A/B restart from their saved 'prev'); a rerun is the way to repair a bad roll, never hand-editing history files.
- After every roll check docs/data for NaN (`grep -l NaN docs/data/*.json`) and that research_data/etf_daily.csv has the Friday row. Yahoo may publish the .DE/.AS Friday closes late; the per-ticker fallback fills them, otherwise the Saturday roll stops and Sunday retries.
- Sanity-check extreme stock moves against a second public quote before calling them bugs (DELL −23% 9–16 Oct was real; PARA at 0.54 USD was a stale ticker).
- Dashboard sync: dataset 'updated' times in meta.json change every run even when content doesn't; sync the files that `git diff --name-only <last synced commit> HEAD -- docs/data` lists (minus meta, archive, *_state).
- Yahoo direct API returns 429 on GitHub runners: use yfinance. Delete any cached etf_daily.csv before offline fixture runs.
- The old 52-week rule's best variant (10-point buffer) won on ETFs but lost on regional data: single-data-set winners are usually luck.
- The meter looked sensible but had zero predictive value since 1927: test any "timing" idea against simply staying invested.
- Keep wording honest: when a rule trails a benchmark (e.g. regional pick 9.8% vs North America 11.0%), say so on the site.
- The dashboard has no record of the last synced commit: list collection datasets with out_dir, take each doc's updated.at, and diff docs/data/<name>.json against `git rev-list -1 --before=<at> HEAD` (skip names without a docs/data file, e.g. plans_*).
- The "IndexPilot weekly pick" task (07:57 UTC) can run before the weekly roll exists and then syncs last week's data; this task re-syncs everything that changed, so always do step 2 fully.
- Yahoo revises Friday closes after the hourly-bar fallback (16 Oct: EUNL 130.445 → 130.54); the Sunday retry picks up the official close. Live tables in LIVE.md use the current etf_daily.csv values.
