# -*- coding: utf-8 -*-
"""生成交互式走势看板（数据内联，双击即可打开，无需服务器）。"""
import json, os
from datetime import date

BASE = r"E:\WB工作区\数据\彩票数据研究_2026"
dlt = json.load(open(os.path.join(BASE, "data", "dlt.json"), encoding="utf-8"))
ssq = json.load(open(os.path.join(BASE, "data", "ssq.json"), encoding="utf-8"))


def pack(rows, prefix, labels, limits, accent):
    periods = [r["期号"] for r in rows]
    dates = [r["开奖日期"] for r in rows]
    nums = []
    for r in rows:
        if prefix == "前区":
            nums.append([r[f"前区{i}"] for i in range(1, 6)] + [r["后区1"], r["后区2"]])
        else:
            nums.append([r[f"红球{i}"] for i in range(1, 7)] + [r["蓝球"]])
    means = [round(sum(x[j] for x in nums) / len(nums), 2) for j in range(7)]
    return {
        "periods": periods, "dates": dates, "nums": nums,
        "labels": labels, "limits": limits, "means": means, "accent": accent,
        "count": len(rows),
    }


DATA = {
    "dlt": pack(dlt, "前区",
                ["前区 1", "前区 2", "前区 3", "前区 4", "前区 5", "后区 1", "后区 2"],
                [35, 35, 35, 35, 35, 12, 12], "#C55221"),
    "ssq": pack(ssq, "红球",
                ["红球 1", "红球 2", "红球 3", "红球 4", "红球 5", "红球 6", "蓝球"],
                [33, 33, 33, 33, 33, 33, 16], "#CC8800"),
}
DATA["dlt"]["title"] = "大乐透"
DATA["ssq"]["title"] = "双色球"
DATA["dlt"]["sub"] = "前区 5 个 · 1—35　+　后区 2 个 · 1—12"
DATA["ssq"]["sub"] = "红球 6 个 · 1—33　+　蓝球 1 个 · 1—16"
DATA["dlt"]["span"] = f'{dlt[0]["期号"]} — {dlt[-1]["期号"]}　|　{dlt[0]["开奖日期"]} → {dlt[-1]["开奖日期"]}'
DATA["ssq"]["span"] = f'{ssq[0]["期号"]} — {ssq[-1]["期号"]}　|　{ssq[0]["开奖日期"]} → {ssq[-1]["开奖日期"]}'

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>开奖号码走势看板 · 大乐透 / 双色球 2026</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2064%2064'%3E%3Crect%20width='64'%20height='64'%20rx='12'%20fill='%2314100C'/%3E%3Ccircle%20cx='32'%20cy='32'%20r='18'%20fill='none'%20stroke='%23CC8800'%20stroke-width='5'/%3E%3Ccircle%20cx='32'%20cy='32'%20r='6'%20fill='%23C55221'/%3E%3C/svg%3E">
<style>
:root{
  --cream:#F5EFE3; --cream-2:#FBF7EF; --paper:#FFFFFF;
  --ink:#14100C; --ink-soft:#3A322A; --muted:#6B6257;
  --amber:#CC8800; --amber-l:#E7A93A; --burnt:#C55221; --burnt-d:#8F3A17;
  --line:rgba(20,16,12,.14); --line-2:rgba(20,16,12,.07);
  --sans:"Bahnschrift","DIN Alternate","Segoe UI","Microsoft YaHei UI","Microsoft YaHei",sans-serif;
  --mono:"JetBrains Mono","Cascadia Mono",Consolas,"Courier New",monospace;
  --ease:cubic-bezier(.22,1,.36,1);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body.mode-entry{overflow:hidden}
body.mode-entry{overflow:hidden}
body{
  margin:0;background:var(--cream);color:var(--ink);
  font-family:var(--sans);font-size:15px;line-height:1.65;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1320px;margin:0 auto;padding:0 32px}
.eyebrow{
  font-family:var(--mono);font-size:11px;letter-spacing:.22em;text-transform:uppercase;
  color:var(--amber);font-weight:600;
}

/* ---------- gate（进门选择层） ---------- */
.gate{
  position:fixed;inset:0;z-index:200;display:grid;place-items:center;padding:28px;overflow:auto;
  background:rgba(8,6,5,.76);
  -webkit-backdrop-filter:blur(38px) saturate(.5) brightness(.42);
  backdrop-filter:blur(38px) saturate(.5) brightness(.42);
  transition:opacity .45s var(--ease),visibility .45s var(--ease);
}
body:not(.mode-entry) .gate{opacity:0;visibility:hidden;pointer-events:none}
.gate::before{content:"";position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(58% 52% at 50% 44%, rgba(204,136,0,.13), transparent 72%)}
.gate-box{position:relative;z-index:1}
.gate::before{content:"";position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(58% 52% at 50% 44%, rgba(204,136,0,.13), transparent 72%)}
.gate-box{position:relative;z-index:1}
.gate-box{width:min(940px,100%)}
.gate-eyebrow{font-family:var(--mono);font-size:10px;letter-spacing:.26em;text-transform:uppercase;
  color:var(--amber);margin-bottom:18px}
.gate-title{font-size:clamp(30px,4.4vw,52px);line-height:1.03;margin:0 0 10px;font-weight:700;
  letter-spacing:-.025em;text-transform:uppercase;color:var(--cream)}
.gate-title em{font-style:normal;color:var(--amber)}
.gate-sub{color:rgba(245,239,227,.55);font-size:13px;margin:0 0 32px;letter-spacing:.04em}
.gate-cards{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.gate-card{
  position:relative;overflow:hidden;text-align:left;cursor:pointer;font-family:var(--sans);
  border:1px solid rgba(245,239,227,.14);padding:26px 26px 22px;color:var(--cream);
  min-height:268px;display:flex;flex-direction:column;
  transition:transform .45s var(--ease),border-color .3s var(--ease),box-shadow .45s var(--ease);
}
.gate-card--dlt{background:linear-gradient(155deg,#C55221 0%,#8F3A17 100%)}
.gate-card--ssq{background:linear-gradient(155deg,#2C2018 0%,#14100C 100%)}
.gate-card:hover{transform:translateY(-7px);border-color:rgba(231,169,58,.72);
  box-shadow:0 26px 64px rgba(0,0,0,.46)}
.gate-card:focus-visible{outline:2px solid var(--amber);outline-offset:3px}
.gc-num{font-family:var(--mono);font-size:10.5px;letter-spacing:.22em;opacity:.62}
.gc-arrow{position:absolute;right:24px;top:24px;font-size:19px;opacity:.4;
  transition:transform .4s var(--ease),opacity .3s var(--ease)}
.gate-card:hover .gc-arrow{transform:translateX(7px);opacity:1}
.gc-name{font-size:clamp(30px,3.2vw,40px);font-weight:700;letter-spacing:-.02em;margin-top:auto;
  line-height:1;text-transform:uppercase}
.gc-en{font-family:var(--mono);font-size:9.5px;letter-spacing:.24em;opacity:.5;margin-top:9px}
.gc-meta{font-size:12.5px;opacity:.8;margin-top:16px;letter-spacing:.03em}
.gc-foot{display:flex;justify-content:space-between;align-items:baseline;margin-top:14px;
  padding-top:13px;border-top:1px solid rgba(245,239,227,.18);
  font-family:var(--mono);font-size:10.5px;letter-spacing:.03em;opacity:.86}
.gc-foot b{font-size:15px;font-weight:600;opacity:1}
.gate-note{margin:28px 0 0;font-size:11.5px;color:rgba(245,239,227,.42);letter-spacing:.04em;
  border-top:1px solid rgba(245,239,227,.12);padding-top:15px}

/* ---------- back ---------- */
.back{
  position:fixed;top:18px;right:22px;z-index:160;
  display:inline-flex;align-items:center;gap:8px;
  border:1px solid rgba(245,239,227,.3);background:rgba(20,16,12,.76);
  color:var(--cream);font-family:var(--sans);font-size:12.5px;letter-spacing:.08em;
  padding:9px 15px;cursor:pointer;-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);
  opacity:0;transform:translateY(-8px);pointer-events:none;
  transition:opacity .4s var(--ease),transform .4s var(--ease),border-color .25s var(--ease);
}
body.mode-dlt .back,body.mode-ssq .back{opacity:1;transform:none;pointer-events:auto}
.back:hover{border-color:var(--amber);background:rgba(30,23,16,.9)}
.back:focus-visible{outline:2px solid var(--amber);outline-offset:2px}

/* ---------- masthead ---------- */
.masthead{background:var(--ink);color:var(--cream);position:relative;overflow:hidden}
.masthead::before{content:"";position:absolute;left:0;right:0;top:0;height:4px;
  background:linear-gradient(90deg,var(--amber),var(--burnt) 55%,var(--ink) 55%)}
.masthead::after{content:"";position:absolute;left:0;right:0;bottom:0;height:1px;
  background:rgba(204,136,0,.42)}
.masthead .wrap{padding:54px 32px 46px}
.mast-top{display:flex;justify-content:space-between;align-items:flex-end;gap:24px;flex-wrap:wrap}
h1{
  font-size:clamp(38px,5.4vw,74px);line-height:.94;margin:14px 0 0;
  font-weight:700;letter-spacing:-.025em;text-transform:uppercase;
}
h1 em{font-style:normal;color:var(--amber)}
.mast-meta{display:flex;gap:44px;flex-wrap:wrap;margin-top:34px;
  border-top:1px solid rgba(245,239,227,.18);padding-top:20px}
.mast-meta div{min-width:120px}
.mast-meta span{display:block;font-family:var(--mono);font-size:10px;letter-spacing:.18em;
  text-transform:uppercase;color:rgba(245,239,227,.5);margin-bottom:4px}
.mast-meta b{font-family:var(--mono);font-size:19px;font-weight:600;letter-spacing:.02em}
.mast-meta small{display:block;color:rgba(245,239,227,.55);font-size:12px;letter-spacing:.02em}
.disclaimer{
  margin-top:22px;font-size:12.5px;color:rgba(245,239,227,.62);
  border-left:2px solid var(--burnt);padding:2px 0 2px 14px;max-width:760px;
}

/* ---------- zone ---------- */
.zone{padding:0 0 76px}
.zone-head{position:relative;overflow:hidden;padding:38px 0 34px}
.zone-head::after{
  content:attr(data-num);position:absolute;right:26px;top:50%;transform:translateY(-50%);
  font-family:var(--mono);font-size:clamp(84px,9vw,132px);font-weight:700;
  line-height:1;color:currentColor;opacity:.055;pointer-events:none;letter-spacing:-.04em;
}
.zone--dlt .zone-head{background:var(--ink);color:var(--cream)}
.zone--ssq .zone-head{background:var(--burnt);color:#FDF3E4}
.zone--ssq .zone-head::before{
  content:"";position:absolute;left:0;right:0;top:0;height:4px;background:var(--amber)}
.zone-title{display:flex;align-items:baseline;gap:18px;flex-wrap:wrap}
.zone-title h2{
  margin:0;font-size:clamp(30px,3.6vw,48px);font-weight:700;letter-spacing:-.02em;
  text-transform:uppercase;line-height:1;
}
.zone-title .cn{font-size:15px;letter-spacing:.4em;opacity:.55;font-weight:400}
.zone-sub{margin:12px 0 0;font-size:13.5px;letter-spacing:.04em;opacity:.72}
.zone-span{margin-top:16px;font-family:var(--mono);font-size:12px;letter-spacing:.06em;opacity:.6}

/* ---------- controls ---------- */
.controls{
  display:flex;gap:18px;align-items:center;flex-wrap:wrap;
  padding:22px 0 16px;border-bottom:1px solid var(--line);margin-bottom:22px;
}
.tabs{display:flex;gap:6px;flex-wrap:wrap}
.tab{
  appearance:none;border:1px solid var(--line);background:transparent;color:var(--ink-soft);
  font-family:var(--sans);font-size:13.5px;letter-spacing:.04em;
  padding:9px 16px;cursor:pointer;position:relative;
  transition:background .28s var(--ease),color .28s var(--ease),
             border-color .28s var(--ease),transform .18s var(--ease);
}
.tab .idx{font-family:var(--mono);font-size:10px;opacity:.45;margin-right:7px;vertical-align:1px}
.tab:hover{border-color:var(--amber);color:var(--ink);transform:translateY(-1px)}
.tab:focus-visible{outline:2px solid var(--amber);outline-offset:2px}
.tab[aria-selected="true"]{
  background:var(--amber);border-color:var(--amber);color:#1A1206;font-weight:600;
}
.tab[aria-selected="true"] .idx{opacity:.7}
.tab--total{padding-right:20px}
.zone--ssq .tab{border-color:rgba(20,16,12,.2)}

.search{display:flex;align-items:center;gap:0;margin-left:auto;
  border:1px solid var(--line);background:var(--paper)}
.search label{font-family:var(--mono);font-size:10px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--muted);padding:0 10px 0 14px}
.search input{
  border:0;background:transparent;font-family:var(--mono);font-size:14px;letter-spacing:.06em;
  padding:10px 8px;width:118px;color:var(--ink);outline:none;
}
.search input::placeholder{color:#B3A897;letter-spacing:.02em;font-size:12px}
.search button{
  border:0;border-left:1px solid var(--line);background:var(--ink);color:var(--cream);
  font-family:var(--sans);font-size:12.5px;letter-spacing:.1em;padding:11px 18px;cursor:pointer;
  transition:background .25s var(--ease);
}
.search button:hover{background:var(--burnt)}
.search button:focus-visible{outline:2px solid var(--amber);outline-offset:2px}
.replay{
  display:inline-flex;align-items:center;gap:8px;border:1px solid var(--line);
  background:transparent;color:var(--ink-soft);cursor:pointer;
  font-family:var(--sans);font-size:12.5px;letter-spacing:.06em;padding:10px 15px;
  transition:border-color .25s var(--ease),color .25s var(--ease);
}
.replay:hover{border-color:var(--amber);color:var(--ink)}
.replay svg{transition:transform .5s var(--ease)}
.replay:hover svg{transform:rotate(-180deg)}
.replay:focus-visible{outline:2px solid var(--amber);outline-offset:2px}

/* ---------- chart card ---------- */
.card{
  background:var(--paper);border:1px solid var(--line);position:relative;
  opacity:0;transform:translateY(18px);
  transition:opacity .6s var(--ease),transform .6s var(--ease);
}
.card.in{opacity:1;transform:none}
.card-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;
  padding:18px 24px 0;flex-wrap:wrap}
.card-head h3{margin:0;font-size:15px;font-weight:600;letter-spacing:.06em}
.card-head h3 span{font-family:var(--mono);color:var(--burnt);margin-right:10px}
.card-head p{margin:4px 0 0;font-size:12px;color:var(--muted);letter-spacing:.03em}
.card-head .live{font-family:var(--mono);font-size:10px;letter-spacing:.16em;
  color:var(--muted);display:flex;align-items:center;gap:7px;text-transform:uppercase}
.card-head .live i{width:6px;height:6px;background:var(--amber);border-radius:50%;
  animation:pulse 1.8s infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.7)}}
.chart{width:100%;height:520px}
.chart--single{height:430px}
#dlt-chart,#ssq-chart{transition:opacity .3s ease}
.fade{opacity:0}

.card-foot{display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;
  border-top:1px solid var(--line-2);padding:12px 24px;font-size:11.5px;color:var(--muted)}
.card-foot .legend{display:flex;gap:16px;flex-wrap:wrap}
.card-foot .legend span{display:flex;align-items:center;gap:6px;font-family:var(--mono);font-size:10.5px}
.card-foot .legend i{width:10px;height:10px;display:block;flex:none}

/* ---------- detail ---------- */
.detail{
  margin-top:18px;border:1px solid var(--line);background:var(--cream-2);
  padding:0 20px;max-height:0;overflow:hidden;opacity:0;
  transition:max-height .5s var(--ease),opacity .35s var(--ease),padding .5s var(--ease);
}
.detail.show{max-height:220px;opacity:1;padding:18px 20px}
.detail-top{display:flex;gap:26px;align-items:baseline;flex-wrap:wrap;margin-bottom:12px}
.detail-top b{font-family:var(--mono);font-size:17px;letter-spacing:.06em}
.detail-top span{font-family:var(--mono);font-size:12px;color:var(--muted);letter-spacing:.05em}
.balls{display:flex;gap:9px;flex-wrap:wrap;align-items:center}
.ball{
  width:40px;height:40px;border-radius:50%;display:grid;place-items:center;
  font-family:var(--mono);font-size:16px;font-weight:700;color:#fff;
  animation:pop .38s var(--ease) backwards;
}
.ball.pre{background:var(--burnt)}
.ball.post{background:var(--ink)}
.ball.blue{background:#1D4ED8}
.ball.sep{width:1px;height:28px;border-radius:0;background:var(--line);animation:none;margin:0 4px}
@keyframes pop{from{transform:scale(.4);opacity:0}to{transform:scale(1);opacity:1}}

/* ---------- footer ---------- */
footer{background:var(--ink);color:rgba(245,239,227,.6);padding:44px 0 54px;font-size:12.5px}
footer .eyebrow{display:block;margin-bottom:16px}
footer p{margin:6px 0;max-width:860px;line-height:1.75}
footer i{color:rgba(245,239,227,.85);font-style:italic}
footer .rule{height:1px;background:rgba(245,239,227,.14);margin:22px 0}

@media(max-width:820px){
  .wrap{padding:0 18px}
  .gate-cards{grid-template-columns:1fr;gap:12px}
  .gate-card{min-height:190px;padding:20px 20px 18px}
  .gc-name{font-size:30px}
  .gate-title{font-size:28px}
  .masthead .wrap{padding:38px 18px 34px}
  .mast-meta{gap:26px}
  .search{margin-left:0;width:100%}
  .search input{flex:1;width:auto}
  .chart{height:420px}
  .chart--single{height:340px}
  .card-head{padding:14px 14px 0}
  .card-foot{padding:10px 14px}
}
@media(prefers-reduced-motion:reduce){
  *{animation-duration:.01ms !important;transition-duration:.01ms !important}
}
</style>
</head>
<body class="mode-entry">

<div class="gate" id="gate" role="dialog" aria-modal="true" aria-label="选择数据板块">
  <div class="gate-box">
    <div class="gate-eyebrow">Select a zone / 选择板块</div>
    <h2 class="gate-title">先选一个<br><em>开奖数据</em></h2>
    <p class="gate-sub">两个彩种各自独立，点进去只看其中一个。</p>
    <div class="gate-cards">
      <button class="gate-card gate-card--dlt" type="button" data-enter="dlt">
        <span class="gc-num">ZONE 01</span>
        <span class="gc-arrow">→</span>
        <span class="gc-name">大乐透</span>
        <span class="gc-en">SUPER LOTTO</span>
        <span class="gc-meta">前区 5 个 · 1—35　+　后区 2 个 · 1—12</span>
        <span class="gc-foot"><span>2026 · 26001 — 26118</span><b>118 期</b></span>
      </button>
      <button class="gate-card gate-card--ssq" type="button" data-enter="ssq">
        <span class="gc-num">ZONE 02</span>
        <span class="gc-arrow">→</span>
        <span class="gc-name">双色球</span>
        <span class="gc-en">DOUBLE COLOR BALL</span>
        <span class="gc-meta">红球 6 个 · 1—33　+　蓝球 1 个 · 1—16</span>
        <span class="gc-foot"><span>2026 · 2026001 — 2026118</span><b>118 期</b></span>
      </button>
    </div>
    <p class="gate-note">仅记录已公布的历史开奖号码与走势，不含任何预测、推荐或投注建议。</p>
  </div>
</div>

<button class="back" id="back" type="button">
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M19 12H5"/><path d="M11 18l-6-6 6-6"/></svg>
  全部板块
</button>

<header class="masthead">
  <div class="wrap">
    <div class="mast-top">
      <div>
        <div class="eyebrow">Lottery Draw Data Study · 2026</div>
        <h1>开奖号码<br><em>走势看板</em></h1>
      </div>
    </div>
    <div class="mast-meta">
      <div><span>统计区间</span><b>01.01 — 10.18</b><small>2026 年</small></div>
      <div><span>大乐透</span><b id="stat-dlt">0</b><small>期开奖记录</small></div>
      <div><span>双色球</span><b id="stat-ssq">0</b><small>期开奖记录</small></div>
      <div><span>数据来源</span><b>官方公告</b><small>体彩 · 福彩</small></div>
    </div>
    <p class="disclaimer">本页仅对已公布的历史开奖号码做记录与可视化，不含任何预测、推荐或投注建议。图中虚线为全期算术平均值，属描述统计量，不代表未来结果。</p>
  </div>
</header>

<main>
  <section class="zone zone--dlt" id="dlt">
    <div class="zone-head" data-num="01">
      <div class="wrap">
        <div class="eyebrow" style="color:var(--amber)">Zone 01 / 体育彩票</div>
        <div class="zone-title"><h2>大乐透</h2><span class="cn">超级大乐透</span></div>
        <p class="zone-sub" id="dlt-sub"></p>
        <p class="zone-span" id="dlt-span"></p>
      </div>
    </div>
    <div class="wrap">
      <div class="controls">
        <div class="tabs" role="tablist" aria-label="大乐透视图切换" data-zone="dlt"></div>
        <div class="search">
          <label for="dlt-q">期号查询</label>
          <input id="dlt-q" list="dlt-list" placeholder="如 26118" autocomplete="off">
          <datalist id="dlt-list"></datalist>
          <button type="button" data-locate="dlt">定位</button>
        </div>
        <button class="replay" type="button" data-replay="dlt" aria-label="重播绘制动画">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 12a9 9 0 1 1-2.64-6.36"/><path d="M21 3v6h-6"/></svg>
          重播
        </button>
      </div>

      <div class="card" id="dlt-card">
        <div class="card-head">
          <div>
            <h3><span id="dlt-idx">01</span><span id="dlt-name">总走势</span></h3>
            <p id="dlt-desc">七个号码按位置顺序逐期衔接，从第 1 期连续绘制到第 118 期</p>
          </div>
          <div class="live"><i></i><span id="dlt-mode">All 118 draws</span></div>
        </div>
        <div class="chart" id="dlt-chart" role="img" aria-label="大乐透号码走势折线图"></div>
        <div class="card-foot">
          <div class="legend" id="dlt-legend"></div>
          <div id="dlt-hint">悬停看数值 · 点击任意位置框出该期 · 再点同一条取消 · 滚轮缩放</div>
        </div>
      </div>

      <div class="detail" id="dlt-detail">
        <div class="detail-top"><b id="dlt-dp">—</b><span id="dlt-dd">—</span></div>
        <div class="balls" id="dlt-balls"></div>
      </div>
    </div>
  </section>

  <section class="zone zone--ssq" id="ssq">
    <div class="zone-head" data-num="02">
      <div class="wrap">
        <div class="eyebrow" style="color:#FFD98A">Zone 02 / 福利彩票</div>
        <div class="zone-title"><h2>双色球</h2><span class="cn">双色球</span></div>
        <p class="zone-sub" id="ssq-sub"></p>
        <p class="zone-span" id="ssq-span"></p>
      </div>
    </div>
    <div class="wrap">
      <div class="controls">
        <div class="tabs" role="tablist" aria-label="双色球视图切换" data-zone="ssq"></div>
        <div class="search">
          <label for="ssq-q">期号查询</label>
          <input id="ssq-q" list="ssq-list" placeholder="如 2026118" autocomplete="off">
          <datalist id="ssq-list"></datalist>
          <button type="button" data-locate="ssq">定位</button>
        </div>
        <button class="replay" type="button" data-replay="ssq" aria-label="重播绘制动画">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 12a9 9 0 1 1-2.64-6.36"/><path d="M21 3v6h-6"/></svg>
          重播
        </button>
      </div>

      <div class="card" id="ssq-card">
        <div class="card-head">
          <div>
            <h3><span id="ssq-idx">01</span><span id="ssq-name">总走势</span></h3>
            <p id="ssq-desc">七个号码按位置顺序逐期衔接，从第 1 期连续绘制到第 118 期</p>
          </div>
          <div class="live"><i></i><span id="ssq-mode">All 118 draws</span></div>
        </div>
        <div class="chart" id="ssq-chart" role="img" aria-label="双色球号码走势折线图"></div>
        <div class="card-foot">
          <div class="legend" id="ssq-legend"></div>
          <div id="ssq-hint">悬停看数值 · 点击任意位置框出该期 · 再点同一条取消 · 滚轮缩放</div>
        </div>
      </div>

      <div class="detail" id="ssq-detail">
        <div class="detail-top"><b id="ssq-dp">—</b><span id="ssq-dd">—</span></div>
        <div class="balls" id="ssq-balls"></div>
      </div>
    </div>
  </section>
</main>

<footer>
  <div class="wrap">
    <span class="eyebrow">Sources &amp; Notes</span>
    <p>数据来源：中国体育彩票官方网站「超级大乐透」历史开奖公告；中国福利彩票官方网站「双色球」历史开奖公告。数据截至 {LAST_DLT} 期（{LAST_DATE}）。</p>
    <p>引用：中国体育彩票. “超级大乐透历史开奖公告.” <i>中国体育彩票</i>, 国家体育总局体育彩票管理中心, webapi.sporttery.cn. 2026 年 10 月 18 日访问.</p>
    <p>引用：中国福利彩票. “双色球历史开奖公告.” <i>中国福利彩票</i>, 中国福利彩票发行管理中心, www.cwl.gov.cn. 2026 年 10 月 18 日访问.</p>
    <div class="rule"></div>
    <p>说明：区间内春节（2 月中旬）与国庆（10 月初）休市造成的日期空档不属于数据缺失。所有均值、极值均为对所载 118 期开奖号码的描述统计。</p>
  </div>
</footer>

<script src="assets/echarts.min.js"></script>
<script>
const DATA = __DATA__;

/* 7 个位次：暖色家族 + 形状双通道编码（编辑设计里黑白也能分辨） */
const POS = [
  {c:'#8F3A17', s:'circle'},
  {c:'#C55221', s:'rect'},
  {c:'#E07B39', s:'triangle'},
  {c:'#CC8800', s:'diamond'},
  {c:'#D9A227', s:'roundRect'},
  {c:'#6E5A1E', s:'pin'},
  {c:'#2E2415', s:'arrow'}
];
const INK='#14100C', MUTED='#6B6257', LINE='rgba(20,16,12,.10)';
const state = {dlt:{view:'total', zoom:null}, ssq:{view:'total', zoom:null}};
const charts = {};

function fmtNum(n){ return n<10 ? '0'+n : ''+n; }

function tabDefs(d){
  const t = [{id:'total', label:'总走势', idx:'01', desc:'七个号码按位置顺序逐期衔接，从第 1 期连续绘制到第 ' + d.count + ' 期', mode:'All ' + d.count + ' draws'}];
  d.labels.forEach((l,i)=>{
    t.push({id:'p'+(i+1), label:'第 '+ (i+1) +' 位', idx:fmtNum(i+2),
      desc: l + ' 单个位次逐期走势，纵向范围 ' + 1 + '—' + d.limits[i],
      mode: 'Position ' + (i+1) + ' / 7'});
  });
  return t;
}

/* ---------- tooltip ---------- */
function totalTip(zone, p){
  const v = p.value, d = DATA[zone];
  const per = v[2], pos = v[3], val = v[1];
  const gi = d.periods.indexOf(per), date = d.dates[gi];
  const all = d.nums[gi];
  const rows = all.map((n,i)=>{
    const on = i === pos;
    return '<span class="tt-row' + (on?' on':'') + '"><i style="background:' + POS[i].c + '"></i>'
      + d.labels[i] + '<b>' + fmtNum(n) + '</b></span>';
  }).join('');
  return '<div class="tt"><div class="tt-h">第 ' + per + ' 期<span>' + date + '</span></div>'
    + '<div class="tt-grid">' + rows + '</div>'
    + '<div class="tt-f">当前点位 · ' + d.labels[pos] + ' = ' + fmtNum(val) + '</div></div>';
}
function singleTip(zone, p){
  const d = DATA[zone], i = p.dataIndex;
  const posIdx = parseInt(state[zone].view.slice(1), 10) - 1;
  const val = d.nums[i][posIdx];
  return '<div class="tt tt--one"><div class="tt-h">第 ' + d.periods[i] + ' 期<span>' + d.dates[i] + '</span></div>'
    + '<div class="tt-one"><i style="background:' + POS[posIdx].c + '"></i>'
    + '<span class="tt-one-l">' + d.labels[posIdx] + '</span>'
    + '<b>' + fmtNum(val) + '</b></div>'
    + '<div class="tt-f">该位次本期开奖号码</div></div>';
}

/* ---------- option builders ---------- */
function baseAxisStyle(){
  return {
    axisLine:{lineStyle:{color:'rgba(20,16,12,.25)'}},
    axisTick:{show:false},
    axisLabel:{color:MUTED, fontFamily:'JetBrains Mono, Consolas, monospace', fontSize:10},
    splitLine:{lineStyle:{color:LINE, type:'solid'}}
  };
}

function totalOption(zone){
  const d = DATA[zone], N = d.count;
  const lineData = [];
  const scatters = POS.map((p, j)=>({ name:d.labels[j], type:'scatter', z:4,
    symbol:p.s, symbolSize:5.2, itemStyle:{color:p.c}, emphasis:{scale:2.4},
    data:[] }));
  for(let i=0;i<N;i++){
    for(let j=0;j<7;j++){
      const x = i*7+j, y = d.nums[i][j];
      lineData.push([x,y]);
      scatters[j].data.push({value:[x,y,d.periods[i],j,d.dates[i]], itemStyle:{color:POS[j].c}});
    }
  }
  return {
    animation:true, animationDuration:2600, animationEasing:'cubicInOut',
    animationDurationUpdate:600,
    grid:{left:52, right:22, top:22, bottom:66, containLabel:false},
    tooltip:{
      trigger:'item', confine:true, backgroundColor:'#14100C', borderWidth:0,
      padding:0, extraCssText:'box-shadow:0 18px 44px rgba(20,16,12,.28);border-radius:0;',
      transitionDuration:0,
      formatter:(p)=> totalTip(zone, p)
    },
    xAxis:Object.assign({}, baseAxisStyle(), {
      type:'value', min:0, max:N*7-1, interval:70, splitLine:{show:false},
      axisLabel:Object.assign({}, baseAxisStyle().axisLabel, {
        interval:0, formatter:(v)=>{
          const gi = Math.round(v/7);
          return (gi >= 0 && gi < N) ? d.periods[gi] : '';
        }
      })
    }),
    yAxis:Object.assign({}, baseAxisStyle(), {
      type:'value', min:0, max:Math.max.apply(null,d.limits)+0.6,
      interval:(Math.max.apply(null,d.limits)<=12?3:(Math.max.apply(null,d.limits)<=16?4:5)),
      splitNumber:6, nameTextStyle:{color:MUTED,fontSize:10},
      axisLabel:Object.assign({}, baseAxisStyle().axisLabel, {showMaxLabel:false})
    }),
    dataZoom:[
      {type:'inside', throttle:40, filterMode:'none'},
      {type:'slider', height:12, bottom:12, borderColor:'transparent',
       backgroundColor:'rgba(20,16,12,.03)', fillerColor:'rgba(204,136,0,.13)',
       handleStyle:{color:'#CC8800', borderColor:'#CC8800'}, moveHandleStyle:{color:'#CC8800'},
       dataBackground:{show:false},
       selectedDataBackground:{show:false},
       textStyle:{color:MUTED,fontSize:9,fontFamily:'Consolas'},
       labelFormatter:(v)=>{ const gi=Math.round(v/7); return (gi>=0&&gi<N)? d.periods[gi] : ''; }}
    ],
    series:[
      { id:'main-line', name:'连续折线', type:'line', data:lineData, showSymbol:false, smooth:false,
        lineStyle:{width:0.9, color:'rgba(20,16,12,.30)'}, z:2, silent:true,
        animationDuration:2600, animationEasing:'cubicInOut', sampling:'none',
        markArea: (state[zone].selected == null) ? undefined : markAreaOf(zone, state[zone].selected) },
      ...scatters
    ]
  };
}

function singleOption(zone, posIdx){
  const d = DATA[zone];
  const vals = d.nums.map(r=>r[posIdx]);
  const mean = d.means[posIdx];
  return {
    animation:true, animationDuration:2400, animationEasing:'cubicInOut',
    animationDurationUpdate:600,
    grid:{left:50, right:20, top:24, bottom:72},
    tooltip:{
      trigger:'axis', confine:true, backgroundColor:'#14100C', borderWidth:0, padding:0,
      extraCssText:'box-shadow:0 18px 44px rgba(20,16,12,.28);border-radius:0;',
      transitionDuration:0,
      axisPointer:{type:'line', lineStyle:{color:'rgba(204,136,0,.5)', width:1, type:'dashed'}},
      formatter:(ps)=> singleTip(zone, ps[0])
    },
    xAxis:Object.assign({}, baseAxisStyle(), {
      type:'category', data:d.periods, boundaryGap:false, splitLine:{show:false},
      axisLabel:Object.assign({}, baseAxisStyle().axisLabel, {
        interval:'auto', rotate:0, hideOverlap:true
      })
    }),
    yAxis:Object.assign({}, baseAxisStyle(), {
      type:'value', min:0, max:d.limits[posIdx]+0.6,
      interval:(d.limits[posIdx]<=12?3:(d.limits[posIdx]<=16?4:5)),
      splitNumber:6, nameTextStyle:{color:MUTED,fontSize:10}, nameGap:16,
      axisLabel:Object.assign({}, baseAxisStyle().axisLabel, {showMaxLabel:false})
    }),
    dataZoom:[
      {type:'inside', throttle:40},
      {type:'slider', height:12, bottom:12, borderColor:'transparent',
       backgroundColor:'rgba(20,16,12,.03)', fillerColor:'rgba(204,136,0,.13)',
       handleStyle:{color:'#CC8800', borderColor:'#CC8800'}, moveHandleStyle:{color:'#CC8800'},
       dataBackground:{show:false},
       selectedDataBackground:{show:false},
       textStyle:{color:MUTED,fontSize:9,fontFamily:'Consolas'}}
    ],
    series:[{
      name:d.labels[posIdx], type:'line', data:vals, smooth:false,
      symbol:'circle', symbolSize:7, showSymbol:true,
      lineStyle:{width:1.9, color:'#C55221'},
      itemStyle:{color:'#CC8800', borderColor:'#fff', borderWidth:1},
      emphasis:{scale:2.2, itemStyle:{color:'#8F3A17'}},
      areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[
        {offset:0,color:'rgba(197,82,33,.18)'},{offset:1,color:'rgba(197,82,33,0)'}])},
      markLine:{
        silent:true, symbol:'none',
        lineStyle:{color:'rgba(143,58,23,.55)', type:'dashed', width:1},
        label:{show:false},
        data:[{yAxis:mean}]
      },
      markPoint:{ symbol:'circle', symbolSize:0, data:[] }
    }]
  };
}

/* ---------- render ---------- */
function render(zone, animate){
  const d = DATA[zone], st = state[zone];
  const chart = charts[zone];
  if(!chart) return;
  const opt = st.view === 'total' ? totalOption(zone) : singleOption(zone, parseInt(st.view.slice(1),10)-1);
  if(!animate){ opt.animation = false; opt.animationDurationUpdate = 0; }
  chart.dispatchAction({type:'hideTip'});
  chart.setOption(opt, true);   // 用 notMerge 整体替换，不要先 clear()：clear 会把 tooltip 内容销毁但组件仍在监听鼠标
  if(st.zoom){ applyZoom(zone, st.zoom, false); }
}

function applyZoom(zone, z, animate){
  charts[zone].dispatchAction({type:'dataZoom', startValue:z[0], endValue:z[1]});
}

function setView(zone, view){
  const d = DATA[zone];
  state[zone].view = view;
  state[zone].zoom = null;
  state[zone].selected = null;   // 换视图时清掉框选
  const defs = tabDefs(d);
  const cur = defs.find(t=>t.id===view);
  document.querySelectorAll('#'+zone+' .tab').forEach(b=>{
    b.setAttribute('aria-selected', b.dataset.view === view ? 'true' : 'false');
  });
  document.getElementById(zone+'-idx').textContent = cur.idx;
  document.getElementById(zone+'-name').textContent = cur.label === '总走势' ? '总走势' : cur.label + ' · 单点走势';
  document.getElementById(zone+'-desc').textContent = cur.desc;
  document.getElementById(zone+'-mode').textContent = cur.mode;
  const el = document.getElementById(zone+'-chart');
  el.classList.toggle('chart--single', view !== 'total');
  el.classList.add('fade');
  setTimeout(()=>{
    charts[zone].resize();
    render(zone, true);
    el.classList.remove('fade');
  }, 170);
  buildLegend(zone, view);
}

function buildLegend(zone, view){
  const d = DATA[zone], box = document.getElementById(zone+'-legend');
  if(view === 'total'){
    box.innerHTML = POS.map((p,i)=>'<span><i style="background:'+p.c+'"></i>'+d.labels[i]+'</span>').join('');
  }else{
    const i = parseInt(view.slice(1),10)-1;
    box.innerHTML = '<span><i style="background:#C55221"></i>'+d.labels[i]+' 实际开奖号码</span>'
      + '<span><i style="background:#8F3A17"></i>全期算术平均 '+d.means[i].toFixed(2)+'（描述统计，非预测）</span>';
  }
}

/* ---------- tabs / search ---------- */
function initTabs(zone){
  const d = DATA[zone], host = document.querySelector('.tabs[data-zone="'+zone+'"]');
  host.innerHTML = tabDefs(d).map(t=>
    '<button class="tab'+(t.id==='total'?' tab--total':'')+'" role="tab" data-view="'+t.id+'" aria-selected="false">'
    + '<span class="idx">'+t.idx+'</span>'+t.label+'</button>').join('');
  host.querySelectorAll('.tab').forEach(btn=>{
    btn.addEventListener('click', ()=> setView(zone, btn.dataset.view));
    btn.addEventListener('keydown', (e)=>{
      const list = Array.from(host.querySelectorAll('.tab'));
      const i = list.indexOf(btn);
      if(e.key==='ArrowRight'){ e.preventDefault(); list[(i+1)%list.length].focus(); }
      if(e.key==='ArrowLeft'){ e.preventDefault(); list[(i-1+list.length)%list.length].focus(); }
    });
  });
  host.querySelector('.tab').setAttribute('aria-selected','true');
  const dl = document.getElementById(zone+'-list');
  dl.innerHTML = d.periods.slice().reverse().map(p=>'<option value="'+p+'">').join('');
}

function locate(zone){
  const d = DATA[zone];
  const raw = document.getElementById(zone+'-q').value.trim();
  if(!raw){ return; }
  let idx = d.periods.indexOf(raw);
  if(idx < 0){ const hit = d.periods.findIndex(p=>p.indexOf(raw)>-1); idx = hit; }
  if(idx < 0){ flash(zone, '未找到该期号'); return; }
  showDetail(zone, idx);
  const st = state[zone];
  if(st.view === 'total'){
    const c = idx*7;
    applyZoom(zone, [c-28, c+28]);
  }else{
    applyZoom(zone, [Math.max(0, idx-12), Math.min(d.count-1, idx+12)]);
  }
  document.getElementById(zone+'-q').blur();
}

function flash(zone, msg){
  const el = document.getElementById(zone+'-hint');
  const old = el.textContent;
  el.textContent = msg;
  el.style.color = '#C55221';
  setTimeout(()=>{ el.textContent = old; el.style.color = ''; }, 1800);
}

function showDetail(zone, idx){
  const d = DATA[zone], box = document.getElementById(zone+'-detail');
  document.getElementById(zone+'-dp').textContent = '第 ' + d.periods[idx] + ' 期';
  document.getElementById(zone+'-dd').textContent = d.dates[idx] + '　·　共 7 个号码';
  const all = d.nums[idx], total = d.limits.length;
  const balls = all.map((n,i)=>{
    let cls = 'ball ';
    if(zone==='dlt') cls += i<5 ? 'pre' : 'post';
    else cls += i<6 ? 'pre' : 'blue';
    const sep = (zone==='dlt' && i===5) ? '<span class="ball sep"></span>' : '';
    return sep + '<span class="' + cls + '" style="animation-delay:' + (i*55) + 'ms">' + fmtNum(n) + '</span>';
  }).join('');
  document.getElementById(zone+'-balls').innerHTML = balls;
  box.classList.add('show');
}

function tipText(){
  const vis = [...document.querySelectorAll('.tt')].filter(t => t.offsetParent !== null);
  if(!vis.length) return '';
  return vis[vis.length - 1].innerText.split(String.fromCharCode(10)).join(' / ');
}

function mountChart(zone, animate){
  const el = document.getElementById(zone + '-chart');
  if(charts[zone]){ charts[zone].dispose(); charts[zone] = null; }
  charts[zone] = echarts.init(el, null, {renderer:'canvas'});
  charts[zone].getZr().on('click', (e)=> onCanvasClick(zone, e.offsetX, e.offsetY));
  render(zone, animate !== false);
}

/* ---------- 图表点击 → 下方详情联动 ---------- */
function onCanvasClick(zone, x, y){
  const chart = charts[zone], d = DATA[zone], st = state[zone];
  if(!chart) return;
  let pt = null;
  try { pt = chart.convertFromPixel({gridIndex:0}, [x, y]); } catch(e){ return; }
  if(!pt) return;
  // 总走势：x 是全局点位序号（每期 7 个点）；单点视图：x 就是期索引
  const gi = (st.view === 'total') ? Math.round(pt[0] / 7) : Math.round(pt[0]);
  if(!(gi >= 0 && gi < d.count)) return;

  if(st.view === 'total'){
    const wasSelected = st.selected === gi;
    highlightPeriod(zone, gi);
    if(!wasSelected) focusPeriod(zone, gi);
  }
  showDetail(zone, gi);
}

/* 期框配置：把某一期的 7 个点在图上整段框住，并标出期号 */
function markAreaOf(zone, gi){
  const d = DATA[zone];
  if(gi == null) return { data: [] };
  return {
    silent:true, z:1,
    itemStyle:{ color:'rgba(204,136,0,.22)',
                borderColor:'rgba(150,92,0,.95)', borderWidth:1.5 },
    label:{ show:true, position:'insideTop', formatter:d.periods[gi],
            color:'#7A3208', fontSize:9, fontFamily:'Consolas',
            backgroundColor:'rgba(252,247,237,.94)', padding:[2,3], borderRadius:2 },
    emphasis:{ disabled:true },
    data:[[ { xAxis: gi*7 - 0.45, yAxis: 0 },
            { xAxis: gi*7 + 6.45, yAxis: Math.max.apply(null,d.limits) + 1 } ]]
  };
}

/* 全景下一期只有几个像素宽，点了也看不清形状；过窄时自动聚焦到该期附近 */
function focusPeriod(zone, gi){
  const chart = charts[zone], d = DATA[zone];
  if(!chart) return;
  const a = chart.convertToPixel({gridIndex:0}, [0, 0]);
  const b = chart.convertToPixel({gridIndex:0}, [7, 0]);
  if(!a || !b) return;
  const perWidth = Math.abs(b[0] - a[0]);
  if(perWidth >= 24) return;                 // 已经够宽，不打断用户当前的缩放
  const lo = Math.max(0, (gi - 9) * 7);
  const hi = Math.min(d.count * 7 - 1, (gi + 9) * 7);
  chart.dispatchAction({type:'dataZoom', startValue: lo, endValue: hi});
}

/* 总走势：把某一期的 7 个点整段框出来，再点同一条取消 */
function highlightPeriod(zone, gi){
  const st = state[zone], chart = charts[zone], d = DATA[zone];
  if(!chart) return;
  st.selected = (st.selected === gi) ? null : gi;
  const s = st.selected;
  chart.setOption({ series:[{ id:'main-line', markArea: markAreaOf(zone, s) }]});
}

/* ---------- 进门 / 返回 ---------- */
function enterZone(zone){
  const other = zone === 'dlt' ? 'ssq' : 'dlt';
  document.body.classList.remove('mode-entry');
  document.body.classList.add('mode-' + zone);
  if(charts[other]){
    charts[other].dispatchAction({type:'hideTip'});
    charts[other].dispose();
    charts[other] = null;
  }
  document.getElementById(other).style.display = 'none';
  document.getElementById(zone).style.display = '';
  window.scrollTo(0, 0);
  setTimeout(()=>{
    const el = document.getElementById(zone);
    document.getElementById(zone+'-card').classList.add('in');
    el.scrollIntoView({behavior:'smooth', block:'start'});
    mountChart(zone, true);
    document.getElementById('back').focus({preventScroll:true});
  }, 430);
}

function exitGate(){
  if(document.body.classList.contains('mode-entry')) return;
  document.body.classList.remove('mode-dlt','mode-ssq');
  document.body.classList.add('mode-entry');
  ['dlt','ssq'].forEach(z=>{
    document.getElementById(z).style.display = '';
    document.getElementById(z+'-card').classList.add('in');
  });
  window.scrollTo({top:0, behavior:'smooth'});
  setTimeout(()=>{
    ['dlt','ssq'].forEach(z=>{
      if(!charts[z]) mountChart(z, false);
      else charts[z].resize();
    });
    const first = document.querySelector('[data-enter]');
    if(first) first.focus({preventScroll:true});
  }, 470);
}

/* ---------- boot ---------- */
function boot(){
  document.getElementById('dlt-sub').textContent = DATA.dlt.sub;
  document.getElementById('ssq-sub').textContent = DATA.ssq.sub;
  document.getElementById('dlt-span').textContent = DATA.dlt.span;
  document.getElementById('ssq-span').textContent = DATA.ssq.span;

  ['dlt','ssq'].forEach(zone=>{
    initTabs(zone);
    buildLegend(zone, 'total');
    document.querySelector('[data-replay="'+zone+'"]').addEventListener('click', ()=> render(zone, true));
    document.querySelector('[data-locate="'+zone+'"]').addEventListener('click', ()=> locate(zone));
    document.getElementById(zone+'-q').addEventListener('keydown', (e)=>{
      if(e.key==='Enter'){ e.preventDefault(); locate(zone); }
    });
    mountChart(zone, false);
  });

  /* 进门选择层 */
  document.querySelectorAll('[data-enter]').forEach(b=>{
    b.addEventListener('click', ()=> enterZone(b.dataset.enter));
  });
  document.getElementById('back').addEventListener('click', exitGate);
  document.addEventListener('keydown', (e)=>{
    if(e.key === 'Escape' && !document.body.classList.contains('mode-entry')) exitGate();
  });

  /* 滚动进场才绘制，让动画被看见 */
  const io = new IntersectionObserver((entries)=>{
    entries.forEach(en=>{
      if(en.isIntersecting){
        const zone = en.target.id;
        en.target.querySelector('.card').classList.add('in');
        if(charts[zone]) render(zone, true);
        io.unobserve(en.target);
      }
    });
  }, {threshold:0.18});
  ['dlt','ssq'].forEach(z=> io.observe(document.getElementById(z)));

  /* 顶部数字滚动 */
  animateCount(document.getElementById('stat-dlt'), DATA.dlt.count);
  animateCount(document.getElementById('stat-ssq'), DATA.ssq.count);

  window.addEventListener('resize', ()=>{
    Object.keys(charts).forEach(z=>{
      const el = document.getElementById(z+'-chart');
      if(el && el.offsetParent !== null && charts[z]){ try{ charts[z].resize(); }catch(e){} }
    });
  });
}

function animateCount(el, target){
  const t0 = performance.now(), dur = 1100;
  function step(t){
    const p = Math.min(1, (t-t0)/dur);
    const e = 1 - Math.pow(1-p, 3);
    el.textContent = Math.round(target*e);
    if(p<1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

document.addEventListener('DOMContentLoaded', boot);
</script>

<style>
/* tooltip（ECharts formatter 输出） */
.tt{min-width:266px;padding:11px 14px;font-family:"Bahnschrift","Segoe UI","Microsoft YaHei",sans-serif}
.tt--one{min-width:172px}
.tt-one{display:flex;align-items:center;gap:9px;padding:9px 0 5px}
.tt-one i{width:7px;height:7px;display:block;flex:none}
.tt-one-l{font-size:11.5px;color:rgba(245,239,227,.62);letter-spacing:.04em}
.tt-one b{margin-left:auto;font-family:Consolas,monospace;font-size:27px;font-weight:700;
  color:#E7A93A;line-height:1;font-variant-numeric:tabular-nums}
.tt-h{font-family:"JetBrains Mono",Consolas,monospace;font-size:12px;letter-spacing:.08em;
  color:#F5EFE3;display:flex;justify-content:space-between;gap:16px;
  border-bottom:1px solid rgba(245,239,227,.16);padding-bottom:7px;margin-bottom:8px}
.tt-h span{color:rgba(245,239,227,.5);letter-spacing:.02em}
.tt-grid{display:grid;grid-template-rows:repeat(4,auto);grid-auto-flow:column;gap:1px 20px}
.tt-row{display:flex;align-items:center;gap:6px;font-size:11px;color:rgba(245,239,227,.62);
  padding:2px 0;font-family:"Bahnschrift","Microsoft YaHei",sans-serif}
.tt-row i{width:6px;height:6px;display:block;flex:none}
.tt-row b{margin-left:auto;padding-left:10px;font-family:Consolas,monospace;font-size:11.5px;
  color:#F5EFE3;font-weight:600;text-align:right;min-width:26px}
.tt-row.on{color:#E7A93A;background:rgba(204,136,0,.13);margin:0 -7px;padding:2px 7px}
.tt-row.on b{color:#E7A93A;font-size:12.5px}
.tt-f{margin-top:8px;padding-top:7px;border-top:1px solid rgba(245,239,227,.16);
  font-family:Consolas,monospace;font-size:10.5px;color:#CC8800;letter-spacing:.04em}
</style>
</body>
</html>
"""

html = TEMPLATE.replace("{LAST_DLT}", DATA["dlt"]["periods"][-1]).replace("{LAST_DATE}", DATA["dlt"]["dates"][-1])
html = html.replace("__DATA__", json.dumps(DATA, ensure_ascii=False, separators=(",", ":")))
# 同时写两份：中文名给本地双击，index.html 给 GitHub Pages 当入口
for name in ("开奖走势交互看板.html", "index.html"):
    out = os.path.join(BASE, name)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
print("written 开奖走势交互看板.html + index.html", round(len(html) / 1024, 1), "KB")