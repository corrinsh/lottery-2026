import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const SHOTS = path.join(__dirname, 'shots');
fs.rmSync(SHOTS, { recursive: true, force: true });
fs.mkdirSync(SHOTS, { recursive: true });

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const PORT = 9300 + Math.floor(Math.random() * 400);
const PROFILE = path.join(process.env.TEMP, 'edge-cdp-lottery-' + Date.now());
const bs = String.fromCharCode(92);
const URL_ = 'file:///' + encodeURI(path.join(ROOT, '开奖走势交互看板.html').replace(new RegExp(bs + bs, 'g'), '/'));

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const results = [];
let stepName = 'boot';
function check(name, ok, note = '') {
  stepName = name;
  results.push({ name, ok: !!ok, note: String(note).slice(0, 300) });
  console.log((ok ? 'PASS ' : 'FAIL ') + name + (note ? '  | ' + note : ''));
}

const browser = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--hide-scrollbars', '--allow-file-access-from-files',
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${PROFILE}`,
  '--window-size=1600,1000', 'about:blank'
], { stdio: 'ignore' });

let ws, msgId = 0;
const pending = new Map();
const errors = [];

async function connect() {
  let list;
  for (let i = 0; i < 60; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      list = await r.json();
      if (list.find((t) => t.type === 'page')) break;
    } catch { }
    await sleep(250);
  }
  const page = list.find((t) => t.type === 'page');
  ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) {
      const { res, rej } = pending.get(m.id);
      pending.delete(m.id);
      m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result);
    } else if (m.method === 'Runtime.exceptionThrown') {
      errors.push('[' + stepName + '] ' + (m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text));
    } else if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error') {
      errors.push(m.params.entry.text);
    } else if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') {
      errors.push(m.params.args.map((a) => a.value || a.description).join(' '));
    }
  };
}
function send(method, params = {}) {
  const id = ++msgId;
  return new Promise((res, rej) => {
    pending.set(id, { res, rej });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expr) {
  const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) {
    throw new Error('页面异常: ' + (r.exceptionDetails.exception?.description || r.exceptionDetails.text) + ' <<< ' + String(expr).slice(0, 160));
  }
  return r.result.value;
}
async function waitFor(expr, timeout = 15000, label = '') {
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) {
    try { if (await evaluate(expr)) return true; } catch { }
    await sleep(180);
  }
  throw new Error('waitFor timeout: ' + (label || expr).slice(0, 120));
}
async function shot(name, full = false) {
  const r = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: full });
  fs.writeFileSync(path.join(SHOTS, name + '.png'), Buffer.from(r.data, 'base64'));
}

const pixExpr = (id) => `(() => {
  const c = document.querySelector('#${id} canvas');
  if (!c) return 0;
  const ctx = c.getContext('2d');
  const d = ctx.getImageData(0, 0, c.width, c.height).data;
  let n = 0; for (let i = 3; i < d.length; i += 400) if (d[i] > 8) n++;
  return n;
})()`;

const hoverExpr = (id, zoneKey, periodIdx, posIdx, isTotal) => `(() => {
  const el = document.getElementById('${id}');
  const chart = echarts.getInstanceByDom(el);
  const x = ${isTotal ? `${periodIdx} * 7 + ${posIdx}` : periodIdx};
  const p = chart.convertToPixel({seriesIndex:0}, [x, DATA.${zoneKey}.nums[${periodIdx}][${posIdx}]]);
  const r = el.getBoundingClientRect();
  return { x: Math.round(r.left + p[0]), y: Math.round(r.top + p[1]) };
})()`;

async function moveMouse(pt) {
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: pt.x - 36, y: pt.y - 28, button: 'none' });
  await sleep(90);
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: pt.x, y: pt.y, button: 'none' });
}
async function clickAt(pt) {
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: pt.x - 36, y: pt.y - 28, button: 'none' });
  await sleep(90);
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: pt.x, y: pt.y, button: 'none' });
  await sleep(120);
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: pt.x, y: pt.y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: pt.x, y: pt.y, button: 'left', clickCount: 1 });
}

try {
  await connect();
  await send('Runtime.enable');
  await send('Log.enable');
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1600, height: 1000, deviceScaleFactor: 1, mobile: false });

  await send('Page.navigate', { url: URL_ });
  await waitFor(`document.readyState === 'complete' && !!document.getElementById('gate')`, 25000, 'navigate');
  await waitFor(`typeof echarts !== 'undefined' && !!echarts.getInstanceByDom(document.getElementById('dlt-chart'))`, 15000, 'echarts init');
  await sleep(1100);
  await shot('01-进门选择页');

  /* ---------- 进门层 ---------- */
  check('页面加载无 JS 异常', errors.length === 0, errors.slice(0, 3).join(' | '));
  check('进场先显示选择层', await evaluate(`document.body.classList.contains('mode-entry') && getComputedStyle(document.getElementById('gate')).visibility === 'visible'`));
  check('选择层背景做了虚化', (await evaluate(`getComputedStyle(document.getElementById('gate')).backdropFilter`)).includes('blur'),
    await evaluate(`getComputedStyle(document.getElementById('gate')).backdropFilter`));
  check('背景滚动被锁住', (await evaluate(`getComputedStyle(document.body).overflow`)) === 'hidden');
  check('两个悬浮入口都在', await evaluate(`document.querySelectorAll('[data-enter]').length`) === 2);
  check('入口卡片含彩种名与期数', (await evaluate(`document.querySelector('[data-enter="dlt"]').innerText`)).includes('大乐透'),
    (await evaluate(`document.querySelector('[data-enter="dlt"]').innerText`)).replace(/\n/g, ' / '));

  /* ---------- 进入大乐透 ---------- */
  await evaluate(`document.querySelector('[data-enter="dlt"]').click()`);
  await sleep(1600);
  check('进入后 body 切到大乐透模式', await evaluate(`document.body.classList.contains('mode-dlt')`));
  check('双色球区块被隐藏（不再顺序排开）', (await evaluate(`document.getElementById('ssq').style.display`)) === 'none');
  check('选择层已淡出', await evaluate(`getComputedStyle(document.getElementById('gate')).visibility === 'hidden'`));
  check('返回按钮出现', await evaluate(`getComputedStyle(document.getElementById('back')).pointerEvents === 'auto'`));
  const dltTop = await evaluate(`String(Math.round(document.getElementById('dlt').getBoundingClientRect().top))`);
  check('大乐透区已滚到视口', Math.abs(Number(dltTop)) < 40, 'top=' + dltTop);

  await sleep(2600);
  check('大乐透总走势图已绘制', (await evaluate(pixExpr('dlt-chart'))) > 200, 'samples=' + await evaluate(pixExpr('dlt-chart')));
  await shot('02-大乐透总走势');

  // 总走势 hover：仍然展示该期 7 个号码
  let pt = await evaluate(hoverExpr('dlt-chart', 'dlt', 61, 2, true));
  await moveMouse(pt);
  await sleep(750);
  let tip = await evaluate(`tipText()`);
  check('总走势悬停仍显示整期 7 个号码', (tip.match(/前区|后区/g) || []).length >= 7, tip.slice(0, 110));
  await shot('03-总走势悬停');

  /* ---------- 单点视图：tooltip 只给一个号码 ---------- */
  await evaluate(`document.querySelector('.tabs[data-zone="dlt"] .tab[data-view="p7"]').click()`);
  await sleep(3000);
  check('切到第 7 位（后区2）', (await evaluate(`document.getElementById('dlt-name').textContent`)).includes('第 7 位'));

  await evaluate(`echarts.getInstanceByDom(document.getElementById('dlt-chart')).dispatchAction({type:'showTip', seriesIndex:0, dataIndex:50})`);
  await sleep(450);
  tip = await evaluate(`tipText()`);
  const shown = (tip.match(/前区|后区|红球|蓝球/g) || []);
  check('单点视图卡片只显示该位次', shown.length === 1 && tip.includes('后区 2'), tip.slice(0, 110));
  check('单点视图卡片有大号号码值', await evaluate(`!!document.querySelector('.tt-one b')`),
    await evaluate(`document.querySelector('.tt-one b') ? document.querySelector('.tt-one b').textContent : ''`));
  await shot('04-单点悬停只显示一位');

  /* ---------- 点击图表 → 下方详情联动 ---------- */
  const targetIdx = 80;
  const expectPeriod = await evaluate(`DATA.dlt.periods[${targetIdx}]`);
  pt = await evaluate(hoverExpr('dlt-chart', 'dlt', targetIdx, 6, false));
  await clickAt(pt);
  await sleep(700);
  const dpTxt = await evaluate(`document.getElementById('dlt-dp').textContent`);
  const ballCnt = await evaluate(`document.querySelectorAll('#dlt-balls .ball:not(.sep)').length`);
  const ballVals = await evaluate(`[...document.querySelectorAll('#dlt-balls .ball:not(.sep)')].map(b=>b.textContent).join(',')`);
  check('点击第 7 位某点，下方详情切到该期', dpTxt.includes(expectPeriod), dpTxt + ' / 期望 ' + expectPeriod);
  check('详情面板弹出并显示 7 个号码', ballCnt === 7, ballVals);
  await shot('05-点击联动详情');

  // 点另一期，验证会跟着变
  const targetIdx2 = 20;
  const expectPeriod2 = await evaluate(`DATA.dlt.periods[${targetIdx2}]`);
  pt = await evaluate(hoverExpr('dlt-chart', 'dlt', targetIdx2, 6, false));
  await clickAt(pt);
  await sleep(700);
  const dp2 = await evaluate(`document.getElementById('dlt-dp').textContent`);
  check('再点另一期，详情跟着更新', dp2.includes(expectPeriod2), dp2 + ' / 期望 ' + expectPeriod2);

  // 总走势点击也要联动
  await evaluate(`document.querySelector('.tabs[data-zone="dlt"] .tab[data-view="total"]').click()`);
  await sleep(3000);
  const t3 = 90;
  const expectPeriod3 = await evaluate(`DATA.dlt.periods[${t3}]`);
  pt = await evaluate(hoverExpr('dlt-chart', 'dlt', t3, 2, true));
  await clickAt(pt);
  await sleep(700);
  check('总走势点击同样联动详情', (await evaluate(`document.getElementById('dlt-dp').textContent`)).includes(expectPeriod3),
    await evaluate(`document.getElementById('dlt-dp').textContent`) + ' / 期望 ' + expectPeriod3);

  /* ---------- 期号查询仍然可用 ---------- */
  await evaluate(`document.getElementById('dlt-q').value = '26050'; document.querySelector('[data-locate="dlt"]').click()`);
  await sleep(800);
  check('期号查询仍可定位', (await evaluate(`document.getElementById('dlt-dp').textContent`)).includes('26050'));
  await shot('06-期号查询');

  /* ---------- 返回 → 再进双色球 ---------- */
  await evaluate(`document.getElementById('back').click()`);
  await sleep(800);
  check('返回后回到选择层', await evaluate(`document.body.classList.contains('mode-entry') && getComputedStyle(document.getElementById('gate')).visibility === 'visible'`));
  check('返回后两个区块恢复正常布局', await evaluate(`document.getElementById('dlt').style.display === '' && document.getElementById('ssq').style.display === ''`));
  await shot('07-返回选择层');

  await evaluate(`document.querySelector('[data-enter="ssq"]').click()`);
  await sleep(1600);
  check('进入双色球模式', await evaluate(`document.body.classList.contains('mode-ssq')`));
  check('此时大乐透被隐藏', (await evaluate(`document.getElementById('dlt').style.display`)) === 'none');
  await sleep(2800);
  check('双色球总走势已绘制', (await evaluate(pixExpr('ssq-chart'))) > 200, 'samples=' + await evaluate(pixExpr('ssq-chart')));
  await shot('08-双色球总走势');

  await evaluate(`document.querySelector('.tabs[data-zone="ssq"] .tab[data-view="p7"]').click()`);
  await sleep(3000);
  pt = await evaluate(hoverExpr('ssq-chart', 'ssq', 40, 6, false));
  await moveMouse(pt);
  await sleep(750);
  tip = await evaluate(`tipText()`);
  check('双色球第 7 位卡片也只显示蓝球一位', (tip.match(/前区|后区|红球|蓝球/g) || []).length === 1 && tip.includes('蓝球'), tip.slice(0, 110));
  await shot('09-双色球蓝球悬停');

  const sIdx = 60, sPer = await evaluate(`DATA.ssq.periods[${sIdx}]`);
  pt = await evaluate(hoverExpr('ssq-chart', 'ssq', sIdx, 6, false));
  await clickAt(pt);
  await sleep(700);
  check('双色球点击联动详情', (await evaluate(`document.getElementById('ssq-dp').textContent`)).includes(sPer),
    await evaluate(`document.getElementById('ssq-dp').textContent`) + ' / 期望 ' + sPer);
  await shot('10-双色球点击联动');

  check('全程无新增 JS 异常', errors.length === 0, errors.map(e => e.split(String.fromCharCode(10))[0]).join(' || '));

} catch (e) {
  check('测试执行', false, e.message);
} finally {
  fs.writeFileSync(path.join(SHOTS, 'report.json'), JSON.stringify({
    url: URL_, results, errors,
    pass: results.filter((r) => r.ok).length, total: results.length
  }, null, 2));
  console.log('\n== ' + results.filter((r) => r.ok).length + '/' + results.length + ' passed ==');
  try { await send('Browser.close'); } catch { }
  browser.kill();
}
