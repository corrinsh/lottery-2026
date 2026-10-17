import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SHOTS = path.join(__dirname, 'shots');
fs.mkdirSync(SHOTS, { recursive: true });

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const PORT = 9500 + Math.floor(Math.random() * 300);
const PROFILE = path.join(process.env.TEMP, 'edge-online-' + Date.now());
const TARGET = 'https://corrinsh.github.io/lottery-2026/';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = spawn(EDGE, ['--headless=new', '--disable-gpu', '--no-first-run', '--hide-scrollbars',
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${PROFILE}`, '--window-size=1600,1000', 'about:blank'],
  { stdio: 'ignore' });

let ws, id = 0; const pend = new Map(); const errors = [];
async function connect() {
  let list;
  for (let i = 0; i < 60; i++) {
    try { const r = await fetch(`http://127.0.0.1:${PORT}/json/list`); list = await r.json(); if (list.find(t => t.type === 'page')) break; } catch { }
    await sleep(250);
  }
  ws = new WebSocket(list.find(t => t.type === 'page').webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pend.has(m.id)) { pend.get(m.id)(m.result); pend.delete(m.id); }
    else if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
    else if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error') errors.push(m.params.entry.text);
  };
}
const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
async function ev(expr) {
  const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) return 'ERR:' + (r.exceptionDetails.exception?.description || '').split('\n')[0];
  return r.result.value;
}
async function shot(name) {
  const r = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(SHOTS, name + '.png'), Buffer.from(r.data, 'base64'));
}
const pass = [];
function ck(n, ok, note = '') { pass.push({ n, ok }); console.log((ok ? 'PASS ' : 'FAIL ') + n + (note ? ' | ' + note : '')); }

try {
  await connect();
  await send('Runtime.enable'); await send('Log.enable'); await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1600, height: 1000, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: TARGET });
  await sleep(5000);

  ck('线上页面返回标题', (await ev(`document.title`)).includes('走势看板'), await ev(`document.title`));
  ck('index.html 正确加载（进门层存在）', await ev(`!!document.getElementById('gate') && document.body.classList.contains('mode-entry')`));
  ck('ECharts 从仓库加载成功', (await ev(`typeof echarts`)) === 'object');
  ck('数据已内联（118 期）', (await ev(`DATA && DATA.dlt && DATA.dlt.count`)) === 118);
  await shot('online-01-进门页');

  await ev(`document.querySelector('[data-enter="dlt"]').click()`);
  await sleep(4000);
  const pix = await ev(`(() => {
    const c = document.querySelector('#dlt-chart canvas');
    if (!c) return 0;
    const ctx = c.getContext('2d');
    const d = ctx.getImageData(0, 0, c.width, c.height).data;
    let n = 0; for (let i = 3; i < d.length; i += 400) if (d[i] > 8) n++;
    return n;
  })()`);
  ck('线上大乐透走势图已渲染', pix > 200, 'samples=' + pix);
  await shot('online-02-大乐透');

  await ev(`document.querySelector('.tabs[data-zone="dlt"] .tab[data-view="p7"]').click()`);
  await sleep(3200);
  ck('在线切换第 7 位成功', (await ev(`document.getElementById('dlt-name').textContent`)).includes('第 7 位'));
  await shot('online-03-第7位');

  ck('无 JS 异常', errors.length === 0, errors.slice(0, 2).join(' | '));
  console.log('\n== ' + pass.filter(p => p.ok).length + '/' + pass.length + ' passed ==');
} catch (e) {
  ck('执行', false, e.message);
} finally {
  try { await send('Browser.close'); } catch { }
  browser.kill();
}
