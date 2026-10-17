import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const PORT = 9812;
const PROFILE = path.join(process.env.TEMP, 'edge-probe-' + Date.now());
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
const ev = async (expr) => (await send('Runtime.evaluate', { expression: expr, returnByValue: true })).result?.value;

await send('Page.enable'); await send('Runtime.enable');
await send('Page.navigate', { url: URL_ });
await sleep(2500);

const info = await ev(`(() => {
  const r = el => { if(!el) return null; const b = el.getBoundingClientRect();
    return {top:Math.round(b.top+scrollY), h:Math.round(b.height), bg:getComputedStyle(el).backgroundColor, mt:getComputedStyle(el).marginTop, pt:getComputedStyle(el).paddingTop}; };
  return {
    masthead:r(document.querySelector('.masthead')),
    main:r(document.querySelector('main')),
    section:r(document.getElementById('dlt')),
    zoneHead:r(document.querySelector('.zone--dlt .zone-head')),
    eyebrow:r(document.querySelector('.zone--dlt .eyebrow')),
    title:r(document.querySelector('.zone--dlt .zone-title')),
    controls:r(document.querySelector('.zone--dlt .controls')),
    mainMargin:getComputedStyle(document.querySelector('main')).margin,
    sectionMargin:getComputedStyle(document.getElementById('dlt')).marginTop,
    headMargin:getComputedStyle(document.querySelector('.zone--dlt .zone-head')).marginTop,
    gapPx: document.getElementById('dlt').getBoundingClientRect().top - document.querySelector('.masthead').getBoundingClientRect().bottom
  };
})()`);
console.log(JSON.stringify(info, null, 2));
try { await send('Browser.close'); } catch { }
b.kill();
