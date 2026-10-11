# Signal500

A self-updating S&P 500 signals website: this week's buy amount (€40–€200), a signal-strength meter,
10/20/30% return plans, value + momentum stock rankings, a simulated demo account and the backtests behind them.

**Not financial advice.** Backtests, rankings and the demo account are simulations.

## How it runs

| Part | What it does |
|---|---|
| `docs/` | The website (static HTML + JSON data), served by GitHub Pages |
| `scripts/update.py` | Downloads Federal Reserve (FRED) data and the public S&P 500 datasets, recalculates everything, writes `docs/data/*.json` |
| `scripts/weekly_update.py` | The weekly rules: buy amount, meter, rankings, demo account |
| `.github/workflows/update.yml` | Runs the update every weekday after the US close, and the weekly roll every Saturday morning |

No API keys or servers are needed. Everything runs on free GitHub Actions and GitHub Pages.

## One-time setup

1. **Settings → Pages →** Source: *Deploy from a branch*, Branch: `main`, folder `/docs` → Save.
   The site appears at `https://<your-username>.github.io/<repo-name>/` within a minute or two.
2. **Settings → Actions → General → Workflow permissions →** *Read and write permissions* → Save
   (lets the update job commit new data).
3. Optional: **Actions → Update data → Run workflow** to run an update right away.

### Own domain (optional)

Settings → Pages → Custom domain, then add the DNS record your domain registrar asks for (a `CNAME` to `<your-username>.github.io`).

## What updates when

- **Every weekday ~22:30 UTC:** market indicators, monthly signal, S&P 500 chart.
- **Every Saturday 06:00 UTC:** next week's buy amount, signal meter, top/bottom 50 rankings, demo account (closes last week's trades, opens new ones).
- **Fixed research data:** 1990–2026 backtests, return plans, CAPE study. FactSet, CAPE, sentiment and news figures are as of 9 Oct 2026; edit `docs/data/indicators.json` / `news.json` to update them.

GitHub can delay scheduled runs by a few minutes at busy times.
