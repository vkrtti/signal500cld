# IndexPilot admin playbook
Your memory between runs. Keep under two pages; merge or delete outdated lines.

## Map
- Page source: page/body.html (one file: CSS + HTML + JS). It runs in two places:
  1. Site: `python3 tools/build_site.py` wraps it into docs/index.html (head with assets/theme.css, d3 7.9.0 from cdnjs, assets/runtime.js; footer). Never edit docs/index.html by hand.
  2. Dashboard: https://claude.ai/artifact/FDxHtYoKRx211m4hmtTptM, document files/index.html = {"text": <page/body.html>}.
- Page layout (since 2026-10-13): main tabs Overview (`home`), Simulation (`sim`), History (`longrun`, rule vs S&P 500), Free Money :D (`extra`, the Extra profit strategy, renamed by the owner), Method (`strategy`); everything else under the More menu (stocks, demo, indexes, week, news, markets, history/plans/gauges = Research). SX.MAIN lists the main tabs; old #/tab links still work.
- New data (weekly): sim_strategies, sim_growth, sim_buying, live_vs_sp500 (indexpilot.py, with built-in consistency checks against ip_variants/ip_backtest/ip_buying that raise on a mismatch) and hist_regional, hist_regional_years (research.py, checked against hist_rotation). Free Money: free_money_live (indexpilot.py, weekly % since LIVE_START for Free Money, the rule and the S&P 500) and free_money_proxy / free_money_proxy_stats (research.py: US momentum top-minus-bottom decile, half each side, a labelled stand-in because the real picks can't be backtested). Colours: rule = accent, S&P 500 = --sp token, on every chart.
- Page API: `dash.data(name)`, `dash.calc(...)`, `dash.onData(...)`, `dash.setLink('#/'+tab)`. docs/assets/runtime.js lists DATASETS; a new data file must be added there, in docs/data/meta.json, and as a new dashboard dataset doc.
- Pipeline (.github/workflows/update.yml): weekdays 22:30 UTC (update.py + news.py); Saturday 06:00 UTC weekly roll (also indexpilot.py, research.py), Sunday 06:00 UTC retry; manual (GraphQL is blocked, so `gh workflow run` fails; use REST): `gh api -X POST repos/vkrtti/signal500cld/actions/workflows/update.yml/dispatches -f ref=main -f 'inputs[weekly]=true'` (or false for the daily update). List runs: `gh api 'repos/vkrtti/signal500cld/actions/workflows/update.yml/runs?per_page=10' -q '.workflow_runs[]|[.event,.conclusion,.created_at]|@tsv'`. Run logs: read `::notice::`/`::error::` annotations via `gh api repos/vkrtti/signal500cld/check-runs/<job_id>/annotations`.
- scripts/indexpilot.py: pick (score = 52-week return ÷ 52-week volatility, BUFFER 0.25, LIVE_START 2026-10-09), amount tiers, market meter, stock ranking, Extra profit, demo account, backtests. scripts/research.py: Kenneth French history tests. scripts/update.py: FRED gauges, markets. scripts/news.py: RSS titles and links only.
- History files you must never delete or rewrite: docs/data/weekly_history.json (published rows from LIVE_START), demo_state, demo_ledger, extra_ledger, docs/data/archive/.

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
- A weekly run before Friday's close used to decide on an unfinished week (pandas W-FRI bins label the coming Friday). indexpilot.py now drops that week unless offline; mid-week manual weekly runs are safe.
- GitHub scheduled runs had never fired as of 2026-10-12 23:10 UTC (repo created 2026-10-11; the Monday 22:30 UTC run was missing). Check event "schedule" runs every week; dispatch manually when missing. If they still never fire, a fallback scheduler is needed.
- Yahoo direct API returns 429 on GitHub runners: use yfinance. Delete any cached etf_daily.csv before offline fixture runs.
- The old 52-week rule's best variant (10-point buffer) won on ETFs but lost on regional data: single-data-set winners are usually luck.
- The meter looked sensible but had zero predictive value since 1927: test any "timing" idea against simply staying invested.
- Hash links must use '#/'+tab, or the page jumps on load.
- Keep wording honest: when a rule trails a benchmark (e.g. regional pick 9.8% vs North America 11.0%), say so on the site.
