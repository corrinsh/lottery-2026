import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const SHOTS = path.join(__dirname, 'shots');
fs.mkdirSync(SHOTS, { recursive: true });

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const PORT = 9700 + Math.floor(Math.random() * 200);
const PROFILE = path.join(process.env.TEMP, 'edge-box-' + Date.now());
const bs = String.fromCharCode(92);
const URL_ = 'file:///' + encodeURI(path.join(ROOT, 'index.html').replace(new RegExp(bs + bs, 'g'), '/'));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const b = spawn(EDGE, ['--headless=new', '--disable-gpu', '--no-first-run', '--hide-scrollbars',
  '--allow-file-access-from-files', `--remote-debugging-port=${PORT}`, `--user-data-dir=${PROFILE}`,
  '--window-size=1600,1000', 'about:blank'], { stdio: 'ignore' });

let list;
for (let i = 0; i < 60; i++) { try { const r = await fetch(`http://127.0.0.1:${PORT}/json/list`); list = await r.json(); if (list.find(t => t.type === 'page')) break; } catch { } await sleep(250); }
const ws = new WebSocket(list.find(t => t.type === 'page').webSocketDebuggerUrl);
await new Promise(r => (ws.onopen = r));
let id = 0; const pend = new Map(); const errs = [];
ws.onmessage = e => {
  const m = JSON.parse(e.data);
  if (m.id && pend.has(m.id)) { pend.get(m.id)(m.result); pend.delete(m.id); }
  else if (m.method === 'Runtime.exceptionThrown') errs.push((m.params.exceptionDetails.exception?.description || '').split('\n')[0]);
};
const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async (expr) => {
  const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) return 'ERR: ' + (r.exceptionDetails.exception?.description || '').split('\n')[0];
  return r.result.value;
};
async function shot(n) { const r = await send('Page.captureScreenshot', { format: 'png' }); fs.writeFileSync(path.join(SHOTS, n + '.png'), Buffer.from(r.data, 'base64')); }
const res = [];
function ck(n, ok, note = '') { res.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + n + (note ? ' | ' + note : '')); }

async function clickAt(x, y) {
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: x - 30, y: y - 25, button: 'none' });
  await sleep(80);
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y, button: 'none' });
  await sleep(100);
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
}
// 用期序号算页面坐标（总走势：x = i*7 + 3，取该期中间位置；y 取绘图区中部）
const pageXY = (periodIdx) => `(() => {
  const el = document.getElementById('dlt-chart');
  const c = echarts.getInstanceByDom(el);
  const p = c.convertToPixel({gridIndex:0}, [${periodIdx}*7 + 3, 18]);
  const r = el.getBoundingClientRect();
  return { x: Math.round(r.left + p[0]), y: Math.round(r.top + p[1]) };
})()`;
const resetZoom = `(() => {
  const c = echarts.getInstanceByDom(document.getElementById('dlt-chart'));
  c.dispatchAction({type:'dataZoom', start:0, end:100});
  return true;
})()`;
const perWidth = `(() => {
  const c = echarts.getInstanceByDom(document.getElementById('dlt-chart'));
  const a = c.convertToPixel({gridIndex:0},[0,0]);
  const b = c.convertToPixel({gridIndex:0},[7,0]);
  return Math.round(Math.abs(b[0]-a[0])*10)/10;
})()`;
const boxState = `(() => {
  const c = echarts.getInstanceByDom(document.getElementById('dlt-chart'));
  const o = c.getOption();
  const ma = o.series[0].markArea;
  if(!ma || !ma.data || !ma.data.length) return null;
  const d = ma.data[0];
  return { from: d[0].xAxis, to: d[1].xAxis, yTop: d[1].yAxis };
})()`;

await send('Page.enable'); await send('Runtime.enable');
await send('Page.navigate', { url: URL_ });
await sleep(2500);
await ev(`document.querySelector('[data-enter="dlt"]').click()`);
await sleep(3800);

ck('总走势已渲染', (await ev(`!!document.querySelector('#dlt-chart canvas')`)));

await ev(resetZoom); await sleep(600);
let pt = await ev(pageXY(80));
await clickAt(pt.x, pt.y);
await sleep(900);
ck('点击后自动聚焦（每期宽度变大）', (await ev(perWidth)) > 24, 'perWidth=' + await ev(perWidth) + 'px');
await sleep(600);
let st = await ev(boxState);
ck('点击后该期被框出', st && Math.abs(st.from - (80 * 7 - 0.45)) < 0.01 && Math.abs(st.to - (80 * 7 + 6.45)) < 0.01,
  JSON.stringify(st));
ck('框的上沿到顶', st && st.yTop >= 36, st ? 'yTop=' + st.yTop : '');
const detail = await ev(`document.getElementById('dlt-dp').textContent`);
ck('下方详情同步到该期', detail.includes(await ev(`DATA.dlt.periods[80]`)), detail);
await shot('box-01-框选一期');

// 点另一期
await ev(resetZoom); await sleep(700);
pt = await ev(pageXY(30));
await clickAt(pt.x, pt.y);
await sleep(600);
st = await ev(boxState);
ck('改点另一期，框会移动', st && Math.abs(st.from - (30 * 7 - 0.45)) < 0.01, JSON.stringify(st));
await shot('box-02-换一期');

// 再点同一期取消
await ev(resetZoom); await sleep(700);
pt = await ev(pageXY(30));
await clickAt(pt.x, pt.y);
await sleep(600);
st = await ev(boxState);
ck('再点同一条可取消', st === null, JSON.stringify(st));
await shot('box-03-取消');

ck('无 JS 异常', errs.length === 0, errs.slice(0, 2).join(' | '));
console.log('\n== ' + res.filter(Boolean).length + '/' + res.length + ' passed ==');
try { await send('Browser.close'); } catch { }
b.kill();
