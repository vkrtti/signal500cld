// IndexPilot runtime: loads docs/data/*.json and gives the page the small data API it was written against
// (dash.data, dash.calc, dash.onData, dash.colors, dash.setLink).
(function () {
  try { const saved = localStorage.getItem('theme'); if (saved) document.documentElement.dataset.theme = saved; } catch (e) {}
  const DATASETS = ['indicators', 'signal_now', 'spx_weekly', 'history', 'backtest', 'fwd_by_signal', 'cape_buckets',
    'stocks_top', 'stocks_fallen', 'sectors', 'news', 'weekly_now', 'weekly_history', 'weekly_tiers', 'weekly_test',
    'meter_now', 'meter_buckets', 'rank_top', 'rank_bottom', 'demo_positions', 'demo_ledger', 'demo_backtest',
    'plans_summary', 'plans_growth', 'plans_years', 'markets', 'regions', 'regions_years', 'hist_plans', 'hist_plans_growth',
    'hist_weekly_rule', 'hist_factors', 'hist_factor_growth', 'hist_decades', 'index_rank', 'pick_rank', 'ip_backtest', 'ip_buying',
    'ip_growth', 'ip_years', 'ip_periods', 'news_feed', 'hist_rotation', 'hist_rotation_decades'];
  const store = {}, calcs = {}, callbacks = [];
  const css = getComputedStyle(document.documentElement);
  const colors = () => [1, 2, 3, 4, 5, 6, 7, 8].map((i) => css.getPropertyValue('--series-' + i).trim() || '#5b6cf9');
  const run = () => callbacks.forEach((fn) => { try { fn(); } catch (e) { console.error(e); } });
  const dash = {
    colors: colors(),
    data(id) {
      if (calcs[id]) {
        const ins = calcs[id].inputs.map((i) => dash.data(i));
        const bad = ins.find((d) => d.status !== 'ok');
        if (bad) return { status: bad.status, data: [] };
        try { return { status: 'ok', data: calcs[id].fn(...ins.map((d) => d.data)) }; }
        catch (e) { console.error(e); return { status: 'error', data: [], message: String(e) }; }
      }
      return store[id] || { status: 'loading', data: [] };
    },
    calc(id, opts) { calcs[id] = opts; },
    onData(fn) { callbacks.push(fn); try { fn(); } catch (e) { console.error(e); } },
    setLink(name) { try { history.replaceState(null, '', '#' + name); } catch (e) {} },
    params() { return {}; }, setParams() {}, resetParams() {}, refresh() {},
  };
  window.dash = dash;
  const bust = '?v=' + Math.floor(Date.now() / 600000);
  Promise.all(DATASETS.map((id) => fetch('data/' + id + '.json' + bust)
    .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then((d) => { store[id] = { status: 'ok', data: d }; })
    .catch((e) => { store[id] = { status: 'error', data: [], message: String(e) }; })))
    .then(() => { document.documentElement.classList.add('loaded'); run(); });
  let t; window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(run, 150); });
  // theme toggle
  window.toggleTheme = () => {
    const root = document.documentElement; const next = root.dataset.theme === 'dark' ? 'light' : root.dataset.theme === 'light' ? 'dark' : (matchMedia('(prefers-color-scheme: dark)').matches ? 'light' : 'dark');
    root.dataset.theme = next; try { localStorage.setItem('theme', next); } catch (e) {}
    dash.colors = colors(); run();
  };
})();
