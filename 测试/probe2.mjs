import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const PORT = 9843;
const PROFILE = path.join(process.env.TEMP, 'edge-p2-' + Date.now());
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const bs = String.fromCharCode(92);
const URL_ = 'file:///' + encodeURI(path.join(ROOT, '开奖走势交互看板.html').replace(new RegExp(bs + bs, 'g'), '/'));

const b = spawn(EDGE, ['--headless=new', '--disable-gpu', '--no-first-run', '--hide-scrollbars',
  '--allow-file-access-from-files', `--remote-debugging-port=${PORT}`, `--user-data-dir=${PROFILE}`,
  '--window-size=1600,1000', 'about:blank'], { stdio: 'ignore' });

let list;
for (let i = 0; i < 60; i++) { try { const r = await fetch(`http://127.0.0.1:${PORT}/json/list`); list = await r.json(); if (list.find(t => t.type === 'page')) break; } catch { } await sleep(250); }
const ws = new WebSocket(list.find(t => t.type === 'page').webSocketDebuggerUrl);
await new Promise(r => (ws.onopen = r));
let id = 0; const pend = new Map();
ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m.result); pend.delete(m.id); } };
const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async (expr) => {
  const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) return 'ERR: ' + (r.exceptionDetails.exception?.description || r.exceptionDetails.text).split('\n')[0];
  return r.result.value;
};

await send('Page.enable'); await send('Runtime.enable');
await send('Page.navigate', { url: URL_ });
await sleep(2200);
await ev(`document.querySelector('[data-enter="dlt"]').click()`);
await sleep(3200);
await ev(`document.querySelector('.tabs[data-zone="dlt"] .tab[data-view="p7"]').click()`);
await sleep(3200);

console.log('view      :', await ev(`document.getElementById('dlt-name').textContent`));
console.log('trigger   :', await ev(`echarts.getInstanceByDom(document.getElementById('dlt-chart')).getOption().tooltip[0].trigger`));
console.log('seriesN   :', await ev(`echarts.getInstanceByDom(document.getElementById('dlt-chart')).getOption().series.length`));
console.log('val50     :', await ev(`DATA.dlt.nums[50][6]`));
console.log('pixel     :', JSON.stringify(await ev(`(() => {
  const el = document.getElementById('dlt-chart');
  const c = echarts.getInstanceByDom(el);
  const p = c.convertToPixel({seriesIndex:0}, [50, DATA.dlt.nums[50][6]]);
  const r = el.getBoundingClientRect();
  return { rel:[Math.round(p[0]),Math.round(p[1])], page:[Math.round(r.left+p[0]),Math.round(r.top+p[1])], w:el.clientWidth, h:el.clientHeight };
})()`)));

console.log('findHover :', JSON.stringify(await ev(`(() => {
  const el = document.getElementById('dlt-chart');
  const c = echarts.getInstanceByDom(el);
  const p = c.convertToPixel({seriesIndex:0}, [50, DATA.dlt.nums[50][6]]);
  const t = c.getZr().handler.findHover(p[0], p[1]);
  return { found: !!t.target, type: t.target && t.target.type, sid: t.target && t.target.__ecData && t.target.__ecData.seriesIndex, di: t.target && t.target.__ecData && t.target.__ecData.dataIndex };
})()`)));

await ev(`echarts.getInstanceByDom(document.getElementById('dlt-chart')).dispatchAction({type:'showTip', seriesIndex:0, dataIndex:50})`);
await sleep(600);
console.log('after showTip .tt :', JSON.stringify(await ev(`(() => {
  const all = [...document.querySelectorAll('.tt')];
  return all.map(t => ({ vis: t.offsetParent !== null, txt: t.innerText.slice(0,60) }));
})()`)));

try { await send('Browser.close'); } catch { }
b.kill();
