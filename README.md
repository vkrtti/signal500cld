# IndexPilot

A self-updating website that tells a euro investor, each week:

- **which index to buy**: six euro-listed index ETFs (MSCI World, S&P 500, Nasdaq-100, MSCI Europe, MSCI Japan,
  MSCI Emerging Markets) ranked by 52-week return; the leader becomes the main index, but only if it leads the
  current pick by more than 5 percentage points;
- **how much to buy** (€40–€200), set by the world market's distance from its record and US stress gauges;
- **which stocks** of that index rank highest and lowest (value + momentum for the S&P 500, price momentum elsewhere);
- a simulated **demo account**, **headlines** and the **backtests** behind every rule (2012–today on real ETF prices,
  1990–2026 regional data, 100 years of US data).

**Not financial advice.** Backtests, rankings and the demo account are simulations.

## How it runs

| Part | What it does |
|---|---|
| `docs/` | The website (static HTML + JSON data), served by GitHub Pages |
| `scripts/update.py` | Daily: Federal Reserve (FRED) indicators, markets table, US research. Weekly (`--weekly`): runs the IndexPilot roll |
| `scripts/indexpilot.py` | The weekly rules: index pick, amount, meter, stock ranking, demo account, 2012–today backtest (prices from Yahoo Finance via `yfinance`) |
| `scripts/universes.json` | Stock lists per index (Europe, Japan, Nasdaq-100, emerging markets). Review once a year |
| `scripts/news.py` | Headlines (titles and links) from the Fed, ECB, Bank of Japan, CNBC, MarketWatch and Google News |
| `scripts/research.py` | Long-history research from the Kenneth French data library |
| `.github/workflows/update.yml` | Runs every weekday after the US close, and the weekly roll every Saturday morning |

No API keys or servers are needed. Everything runs on free GitHub Actions and GitHub Pages.
ETF price history is cached in `research_data/etf_daily.csv`, so a failed download never loses data.

## One-time setup

1. **Settings → Pages →** Source: *Deploy from a branch*, Branch: `main`, folder `/docs` → Save.
2. **Settings → Actions → General → Workflow permissions →** *Read and write permissions* → Save.
3. Optional: **Actions → Update data → Run workflow** (tick *weekly*) to run the weekly roll right away.

## What updates when

- **Every weekday ~22:30 UTC:** market indicators, markets table, headlines.
- **Every Saturday 06:00 UTC:** index pick, weekly amount, signal meter, stock ranking, demo account, backtests, long-history research.

GitHub can delay scheduled runs by a few minutes at busy times.
