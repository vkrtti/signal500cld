// Usage: (cd tools/test && npm ci) && node tools/test/page_test.js [page/body.html] [docs/data]
// Headless check: runs the dashboard page with a mock `dash` and the real dataset files.
const fs = require('fs'), path = require('path');
const { JSDOM } = require('jsdom');
const root = path.join(__dirname, '..', '..');
const page = process.argv[2] || path.join(root, 'page/body.html'), dataDir = process.argv[3] || path.join(root, 'docs/data');
const html = fs.readFileSync(page, 'utf8');
const dom = new JSDOM(`<!doctype html><html><body><div id="dash-root">${html.replace(/<script>[\s\S]*?<\/script>/g, '')}</div></body></html>`, { runScripts: 'outside-only', pretendToBeVisual: true });
const w = dom.window;
const errors = [];
w.addEventListener('error', (e) => errors.push('window error: ' + e.message));
Object.defineProperty(w.HTMLElement.prototype, 'clientWidth', { get() { return 800; } });
Object.defineProperty(w.HTMLElement.prototype, 'offsetParent', { get() { let el = this; while (el) { if (el.hidden) return null; el = el.parentElement; } return w.document.body; } });
Object.defineProperty(w.HTMLElement.prototype, 'offsetWidth', { get() { return 100; } });
w.SVGElement.prototype.getComputedTextLength = function () { return (this.textContent || '').length * 7; };
w.Element.prototype.scrollIntoView = function () {};
w.eval(fs.readFileSync(path.join(__dirname, 'node_modules/d3/dist/d3.min.js'), 'utf8'));
const files = {}; for (const f of fs.readdirSync(dataDir)) if (f.endsWith('.json')) files[f.replace('.json', '')] = JSON.parse(fs.readFileSync(path.join(dataDir, f), 'utf8'));
const calcs = {}; const cbs = [];
const marksUsed = new Set();
w.dash = {
  colors: ['#1','#2','#3','#4','#5','#6','#7','#8'].map((c, i) => `hsl(${i * 45},60%,50%)`),
  data(id) { marksUsed.add(id); if (calcs[id]) { const c = calcs[id]; const ins = c.inputs.map((i) => this.data(i).data); return { status: 'ok', data: c.fn(...ins) }; } if (!(id in files)) return { status: 'missing', data: [] }; return { status: 'ok', data: files[id], columns: Array.isArray(files[id]) && files[id][0] ? Object.keys(files[id][0]) : [] }; },
  calc(id, o) { calcs[id] = o; }, onData(fn) { cbs.push(fn); fn(); }, setLink() {}, params() { return {}; }, setParams() {}, resetParams() {}, refresh() {},
};
const run = (label, f) => { try { f(); } catch (e) { errors.push(label + ': ' + e.stack.split('\n').slice(0, 3).join(' | ')); } };
for (const m of html.matchAll(/<script>([\s\S]*?)<\/script>/g)) run('script', () => w.eval(m[1]));
const fire = () => cbs.forEach((f) => run('onData', f));
fire();
const SX = w.SX;
for (const t of ['home', 'sim', 'longrun', 'faq', 'indexes', 'week', 'stocks', 'extra', 'demo', 'strategy', 'news', 'markets', 'history', 'plans', 'gauges']) {
  run('show ' + t, () => SX.show(t)); fire();
  const sec = w.document.getElementById(t);
  const empties = [...sec.querySelectorAll('[data-source]')].filter((el) => el.tagName !== 'TABLE' && !el.classList.contains('chart') && el.tagName !== 'UL' && !el.classList.contains('gauge-box') && (el.textContent.trim() === '—' || el.textContent.trim() === ''));
  const tables = [...sec.querySelectorAll('table')].map((tb) => tb.id + ':' + tb.querySelectorAll('tbody tr').length);
  const charts = [...sec.querySelectorAll('.chart,.gauge-box,ul.mini')].map((c) => c.id + ':' + (c.querySelector('svg,li') ? 'drawn' : 'EMPTY'));
  console.log(`[${t}] tables ${tables.join(' ')} | visuals ${charts.join(' ')} | unfilled marks ${empties.length}${empties.length ? ' → ' + empties.slice(0, 6).map((e) => e.dataset.source + '/' + (e.dataset.field || '') + '/' + (e.dataset.where || e.dataset.row || '')).join(', ') : ''}`);
}
// interactions
run('plan 30%', () => { w.document.querySelector('#plan-tabs [data-plan="30%"]').click(); });
run('filter bottom', () => { SX.show('stocks'); w.document.querySelector('#home-filters [data-list="Bottom"]').click(); });
console.log('home rows after Bottom filter:', w.document.querySelectorAll('#home-table tbody tr').length);
run('sector', () => { const b = w.document.querySelector('#home-filters [data-sector]'); b && b.click(); });
console.log('home rows after sector filter:', w.document.querySelectorAll('#home-table tbody tr').length);
run('search', () => { const q = w.document.getElementById('q-home'); q.value = 'tsmc'; q.dispatchEvent(new w.Event('input')); });
console.log('home rows after search:', w.document.querySelectorAll('#home-table tbody tr').length);
run('sort', () => { w.document.querySelector('#home-table th[data-field="price"] button').click(); });
console.log('statusbar:', w.document.getElementById('statusbar').textContent.replace(/\s+/g, ' ').trim());
console.log('takeaway:', w.document.getElementById('takeaway').textContent);
console.log(errors.length ? 'ERRORS:\n' + errors.join('\n') : 'NO ERRORS'); process.exitCode = errors.length ? 1 : 0;
for (const q of ["Which index should I buy this week?", "How much should I invest?", "Top stocks and their weights", "How is the demo account doing?", "Does the strategy work?", "why is there US data", "tell me about TSMC", "how is nasdaq doing", "what is the vix", "what does the buffer mean", "why msci world now?", "what changed?", "how do I buy it", "what is the score", "Japan vs Nasdaq", "is S&P 500 better than world", "what is momentum", "what does volatility mean", "fees and taxes?", "when was the data updated", "what is an ISIN", "what are the weakest stocks", "should I sell?", "what's the market meter saying", "how is the plan doing vs the S&P 500 so far?", "compare all strategies", "how has the rule done over the long run?", "show me the simulation", "blah blah zzz", "hello"]) {
  try { const a = w.SX.askLocal(q); console.log('Q:', q, '\n  A:', a.text.split('\n').slice(0, 3).join(' | ').slice(0, 230), '| go', a.go); } catch (e) { console.log('BOT ERROR', q, e.message); }
}
