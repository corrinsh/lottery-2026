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

// off: 点在当期第几个号码上（0..6）
const pageXY = (periodIdx, off = 3) => `(() => {
  const el = document.getElementById('dlt-chart');
  const c = echarts.getInstanceByDom(el);
  const p = c.convertToPixel({gridIndex:0}, [${periodIdx}*7 + ${off}, 18]);
  const r = el.getBoundingClientRect();
  return { x: Math.round(r.left + p[0]), y: Math.round(r.top + p[1]) };
})()`;
const clearBox = `(() => {
  const c = echarts.getInstanceByDom(document.getElementById('dlt-chart'));
  state.dlt.selected = null;
  c.setOption({series:[{id:'main-line', markArea:{data:[]}}]});
  return true;
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
const boxPeriod = `(() => {
  const c = echarts.getInstanceByDom(document.getElementById('dlt-chart'));
  const o = c.getOption();
  const ma = o.series[0].markArea;
  if(!ma || !ma.data || !ma.data.length) return null;
  const from = ma.data[0][0].xAxis, to = ma.data[0][1].xAxis;
  // 由框的范围反推期号
  return { gi: Math.round((from + 0.45) / 7), from, to };
})()`;
const detailTxt = `document.getElementById('dlt-dp').textContent`;

await send('Page.enable'); await send('Runtime.enable');
await send('Page.navigate', { url: URL_ });
await sleep(2500);
await ev(`document.querySelector('[data-enter="dlt"]').click()`);
await sleep(3800);
ck('总走势已渲染', await ev(`!!document.querySelector('#dlt-chart canvas')`));

/* ---- 同一期不同点位，都应框住同一期（这是之前偏一期的 bug）---- */
for (const off of [0, 1, 3, 5, 6]) {
  await ev(clearBox); await ev(resetZoom); await sleep(650);
  const target = 110 - 118 + 118; // 26110 对应索引 109
  const pt = await ev(pageXY(109, off));
  await clickAt(pt.x, pt.y);
  await sleep(800);
  const box = await ev(boxPeriod);
  const per = await ev(`DATA.dlt.periods[109]`);
  ck(`点第 ${off + 1} 个号（共 7 位）→ 框住 ${per}`, box && box.gi === 109, JSON.stringify(box));
}

/* ---- 框的宽度要跟着缩放走：放大后框应正好包住该期 7 个点 ---- */
await ev(clearBox); await ev(resetZoom); await sleep(650);
const pt0 = await ev(pageXY(109, 2));
await clickAt(pt0.x, pt0.y);
await sleep(1200);
ck('点击后自动聚焦', (await ev(perWidth)) > 24, 'perWidth=' + await ev(perWidth) + 'px');

const fit = await ev(`(() => {
  const c = echarts.getInstanceByDom(document.getElementById('dlt-chart'));
  const ma = c.getOption().series[0].markArea.data[0];
  const left  = c.convertToPixel({gridIndex:0},[ma[0].xAxis,0])[0];
  const right = c.convertToPixel({gridIndex:0},[ma[1].xAxis,0])[0];
  const p0 = c.convertToPixel({gridIndex:0},[109*7,0])[0];
  const p6 = c.convertToPixel({gridIndex:0},[109*7+6,0])[0];
  return { left: Math.round(left), right: Math.round(right),
           p0: Math.round(p0), p6: Math.round(p6), w: Math.round(right-left) };
})()`);
ck('放大后框仍精确包住该期 7 个点', fit && fit.left < fit.p0 && fit.right > fit.p6,
  `框 ${fit.left}~${fit.right}，点位 ${fit.p0}~${fit.p6}，宽 ${fit.w}px`);
ck('框宽随缩放变宽（不是固定像素）', fit && fit.w > 40, 'w=' + (fit ? fit.w : '?') + 'px');
await shot('box-01-框选一期');

/* ---- 期号与框一致 ---- */
const per109 = await ev(`DATA.dlt.periods[109]`);
ck('下方详情显示 26110', (await ev(detailTxt)).includes(per109), await ev(detailTxt));

/* ---- 再点同一条取消 ---- */
const ptc = await ev(pageXY(109, 3));
await clickAt(ptc.x, ptc.y);
await sleep(700);
ck('再点同一条可取消', (await ev(boxPeriod)) === null, JSON.stringify(await ev(boxPeriod)));

/* ---- 换一期 ---- */
await ev(clearBox); await ev(resetZoom); await sleep(650);
const pt2 = await ev(pageXY(30, 6));
await clickAt(pt2.x, pt2.y);
await sleep(800);
const box2 = await ev(boxPeriod);
ck('点 26131 的第 7 位 → 框住 26131', box2 && box2.gi === 30,
  (await ev(`DATA.dlt.periods[30]`)) + ' / ' + JSON.stringify(box2));
await shot('box-02-换一期');

ck('无 JS 异常', errs.length === 0, errs.slice(0, 2).join(' | '));
console.log('\n== ' + res.filter(Boolean).length + '/' + res.length + ' passed ==');
try { await send('Browser.close'); } catch { }
b.kill();
