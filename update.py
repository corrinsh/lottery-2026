# -*- coding: utf-8 -*-
"""增量更新：抓官方最新开奖，有新增期号就并入本地数据并重建全部产物。

设计：每次抓最近一段数据与本地对比，而不是只抓"今天"，这样某天漏跑也能自动补上。
当天不开奖（含官方休市）时自然没有新增，脚本直接跳过重建。
"""
import json, os, sys, subprocess
from datetime import date, datetime, timedelta

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
PY = sys.executable
START = date(2026, 1, 1)
TODAY = date.today()

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def get(url, referer=None, tries=4):
    import urllib.request, time
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer or ""})
    last = None
    for _ in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last = e
            time.sleep(2)
    raise RuntimeError(f"请求失败: {last}")


def load(name):
    p = os.path.join(DATA, name + ".json")
    if not os.path.exists(p):
        return []
    return json.load(open(p, encoding="utf-8"))


def save(name, rows):
    rows.sort(key=lambda r: r["开奖日期"])
    with open(os.path.join(DATA, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)


def fetch_dlt(pages=2):
    out = []
    for page in range(1, pages + 1):
        url = ("https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
               f"?gameNo=85&provinceId=0&pageSize=100&isVerify=1&pageNo={page}")
        js = get(url, "https://www.sporttery.cn/")
        lst = js.get("value", {}).get("list") or []
        if not lst:
            break
        for it in lst:
            d = date.fromisoformat(it["lotteryDrawTime"])
            if d < START:
                continue
            n = it["lotteryDrawResult"].split()
            out.append({
                "期号": it["lotteryDrawNum"], "开奖日期": it["lotteryDrawTime"],
                "前区1": int(n[0]), "前区2": int(n[1]), "前区3": int(n[2]),
                "前区4": int(n[3]), "前区5": int(n[4]),
                "后区1": int(n[5]), "后区2": int(n[6]),
                "前区和值": sum(int(x) for x in n[:5]),
            })
    return out


def fetch_ssq(since):
    import urllib.parse
    out = []
    page = 1
    while page <= 3:
        url = ("https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?"
               + urllib.parse.urlencode({
                   "name": "ssq", "issueCount": "", "issueStart": "", "issueEnd": "",
                   "dayStart": since.isoformat(), "dayEnd": TODAY.isoformat(),
                   "pageNo": page, "pageSize": 100, "week": "", "systemType": "PC"}))
        js = get(url, "https://www.cwl.gov.cn/")
        lst = js.get("result") or []
        if not lst:
            break
        for it in lst:
            d = date.fromisoformat(it["date"][:10])
            if d < START:
                continue
            red = [int(x) for x in it["red"].split(",")]
            out.append({
                "期号": it["code"], "开奖日期": d.isoformat(),
                "红球1": red[0], "红球2": red[1], "红球3": red[2],
                "红球4": red[3], "红球5": red[4], "红球6": red[5],
                "蓝球": int(it["blue"]), "红球和值": sum(red),
            })
        page += 1
    return out


def merge(name, fetched):
    rows = load(name)
    have = {r["期号"] for r in rows}
    added = [r for r in fetched if r["期号"] not in have]
    if added:
        rows.extend(added)
        save(name, rows)
    return rows, sorted(added, key=lambda r: r["开奖日期"])


def run(script):
    r = subprocess.run([PY, os.path.join(BASE, script)], cwd=BASE,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(f"  ! {script} 失败:\n{r.stderr[-800:]}")
        return False
    return True


def main():
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] 检查最新开奖 …")

    dlt_rows, dlt_added = merge("dlt", fetch_dlt())
    last_ssq = (date.fromisoformat(load("ssq")[-1]["开奖日期"]) + timedelta(days=1)) if load("ssq") else START
    ssq_rows, ssq_added = merge("ssq", fetch_ssq(max(START, last_ssq - timedelta(days=10))))

    for label, added, rows in (("大乐透", dlt_added, dlt_rows), ("双色球", ssq_added, ssq_rows)):
        if added:
            items = "、".join(f"{r['期号']}({r['开奖日期']})" for r in added)
            print(f"  {label}: 新增 {len(added)} 期 → {items}")
        else:
            print(f"  {label}: 无新增（本地共 {len(rows)} 期，最新 {rows[-1]['期号']}）")

    total = len(dlt_added) + len(ssq_added)
    if total == 0:
        print("== 无新数据，跳过重建 ==")
        return 0

    print("== 检测到新数据，重建表格与图表 ==")
    ok1 = run("generate.py")
    ok2 = run("build_web.py")

    # 兜底校验：确认最新期号真的写进了 HTML，避免"重建了但没生效"
    if ok2:
        html_path = os.path.join(BASE, "开奖走势交互看板.html")
        with open(html_path, encoding="utf-8") as fh:
            page = fh.read()
        for label, rows in (("大乐透", dlt_rows), ("双色球", ssq_rows)):
            last = rows[-1]["期号"]
            hit = last in page
            print(f"  校验 {label} 最新期 {last} 已写入看板：{'是' if hit else '否'}")
            if not hit:
                ok2 = False
        if ok2:
            print(f"  看板文件 {round(len(page) / 1024, 1)} KB，更新时间 {datetime.now():%Y-%m-%d %H:%M}")

    print("== 完成 ==" if (ok1 and ok2) else "== 重建有异常，请查看上方日志 ==")
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    raise SystemExit(main())
