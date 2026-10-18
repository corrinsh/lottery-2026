import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const SHOTS = path.join(__dirname, 'shots');
fs.mkdirSync(SHOTS, { recursive: true });

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const PORT = 9900 + Math.floor(Math.random() * 90);
const PROFILE = path.join(process.env.TEMP, 'edge-ssq-' + Date.now());
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
  await sleep(70);
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y, button: 'none' });
  await sleep(90);
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
}

const pageXY = (gi, off = 3) => `(() => {
  const el = document.getElementById('ssq-chart');
  const c = echarts.getInstanceByDom(el);
  const p = c.convertToPixel({gridIndex:0}, [${gi}*7 + ${off}, 18]);
  const r = el.getBoundingClientRect();
  return { x: Math.round(r.left + p[0]), y: Math.round(r.top + p[1]) };
})()`;
const resetZoom = `(() => {
  echarts.getInstanceByDom(document.getElementById('ssq-chart')).dispatchAction({type:'dataZoom', start:0, end:100});
  return true;
})()`;
const boxes = `(() => {
  const c = echarts.getInstanceByDom(document.getElementById('ssq-chart'));
  const ma = c.getOption().series[0].markArea;
  if(!ma || !ma.data || !ma.data.length) return [];
  return ma.data.map(d => Math.round((d[0].xAxis + 0.45) / 7));
})()`;

async function hit(gi, off = 3) {
  await ev(resetZoom); await sleep(520);
  const pt = await ev(pageXY(gi, off));
  await clickAt(pt.x, pt.y);
  await sleep(520);
  return await ev(boxes);
}

await send('Page.enable'); await send('Runtime.enable');
await send('Page.navigate', { url: URL_ });
await sleep(2500);
await ev(`document.querySelector('[data-enter="ssq"]').click()`);
await sleep(4000);

ck('双色球总走势已渲染', await ev(`!!document.querySelector('#ssq-chart canvas')`));
ck('双色球提示也提到可多选', (await ev(`document.getElementById('ssq-hint').innerText`)).includes('可多选'),
  await ev(`document.getElementById('ssq-hint').innerText`));

let got = await hit(20);
ck('点第 1 期 → 1 个框', got.length === 1 && got[0] === 20, JSON.stringify(got));

got = await hit(55, 6);
ck('再点第 2 期（第 7 个号位置）→ 两个框并存', got.length === 2 && got.includes(20) && got.includes(55), JSON.stringify(got));

got = await hit(100, 0);
ck('再点第 3 期（第 1 个号位置）→ 三个框', got.length === 3 && got.includes(100), JSON.stringify(got));
ck('提示显示已框选 3 期', (await ev(`document.getElementById('ssq-hint').innerText`)).includes('已框选 3 期'),
  await ev(`document.getElementById('ssq-hint').innerText`));
await shot('ssq-box-01-多选三期');

// 框的纵向范围应覆盖蓝球（1-16）到红球上限
const span = await ev(`(() => {
  const c = echarts.getInstanceByDom(document.getElementById('ssq-chart'));
  const ma = c.getOption().series[0].markArea.data[0];
  return { y0: ma[0].yAxis, y1: ma[1].yAxis };
})()`);
ck('框的纵向覆盖 0 到上限以上', span && span.y0 === 0 && span.y1 >= 34, JSON.stringify(span));

got = await hit(55);
ck('点已框的一期 → 只移除它', got.length === 2 && !got.includes(55), JSON.stringify(got));

await ev(`document.querySelector('#ssq-hint [data-clear]').click()`);
await sleep(400);
ck('清除全部', (await ev(boxes)).length === 0, JSON.stringify(await ev(boxes)));

// 切到单点视图再切回，框应清空
await hit(40);
await ev(`document.querySelector('.tabs[data-zone="ssq"] .tab[data-view="p3"]').click()`);
await sleep(2800);
ck('切到单点视图后框清空', (await ev(`state.ssq.selected.length`)) === 0, 'selected=' + await ev(`JSON.stringify(state.ssq.selected)`));
ck('单点视图提示改为查看号码（不再提框选）',
  (await ev(`document.getElementById('ssq-hint').innerText`)).includes('查看该期开奖号码'),
  await ev(`document.getElementById('ssq-hint').innerText`));
await shot('ssq-box-02-单点视图');

ck('无 JS 异常', errs.length === 0, errs.slice(0, 2).join(' | '));
console.log('\n== ' + res.filter(Boolean).length + '/' + res.length + ' passed ==');
try { await send('Browser.close'); } catch { }
b.kill();
