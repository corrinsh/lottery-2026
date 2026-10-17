import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const PORT = 9761;
const PROFILE = path.join(process.env.TEMP, 'edge-diag-' + Date.now());
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const URL_ = 'file:///' + encodeURI(path.join(ROOT, '开奖走势交互看板.html').replace(/\\/g, '/'))
console.log('URL =', URL_);

const b = spawn(EDGE, ['--headless=new', '--disable-gpu', '--no-first-run',
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${PROFILE}`,
  '--window-size=1600,1000', '--allow-file-access-from-files', 'about:blank'], { stdio: 'ignore' });

let list;
for (let i = 0; i < 60; i++) {
  try { const r = await fetch(`http://127.0.0.1:${PORT}/json/list`); list = await r.json(); if (list.length) break; } catch { }
  await sleep(250);
}
console.log('targets:', list && list.map((t) => t.type + ':' + t.url));
const page = list.find((t) => t.type === 'page');
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pend = new Map();
ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } };
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });

await send('Page.enable'); await send('Runtime.enable');
const nav = await send('Page.navigate', { url: URL_ });
console.log('navigate result:', JSON.stringify(nav).slice(0, 300));
await sleep(3000);
for (const expr of ['location.href', 'document.readyState', 'document.title',
  '"hello"', 'document.body ? document.body.children.length : -1',
  'typeof echarts', '!!document.getElementById("dlt-chart")', 'document.body.innerText.slice(0,120)']) {
  const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true });
  console.log(expr, '=>', JSON.stringify(r.result?.result?.value), r.error ? JSON.stringify(r.error) : '');
}
try { await send('Browser.close'); } catch { }
b.kill();
