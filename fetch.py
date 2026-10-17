# -*- coding: utf-8 -*-
"""抓取 2026-01-01 至今天的大乐透、双色球官方开奖数据（只做数据记录，不做预测）。"""
import json, urllib.request, urllib.parse, time, sys
from datetime import date

START = date(2026, 1, 1)
END = date(2026, 10, 18)
OUT = r"E:\WB工作区\数据\彩票数据研究_2026\data"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def get(url, referer=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer or ""})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("  retry", attempt, e)
            time.sleep(2)
    raise SystemExit("请求失败: " + url)


def fetch_dlt():
    rows, page = [], 1
    while True:
        url = ("https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
               f"?gameNo=85&provinceId=0&pageSize=100&isVerify=1&pageNo={page}")
        js = get(url, "https://www.sporttery.cn/")
        lst = js.get("value", {}).get("list") or []
        if not lst:
            break
        stop = False
        for it in lst:
            d = date.fromisoformat(it["lotteryDrawTime"])
            if d < START:
                stop = True
                continue
            if d > END:
                continue
            nums = it["lotteryDrawResult"].split()
            rows.append({
                "期号": it["lotteryDrawNum"],
                "开奖日期": it["lotteryDrawTime"],
                "前区1": int(nums[0]), "前区2": int(nums[1]), "前区3": int(nums[2]),
                "前区4": int(nums[3]), "前区5": int(nums[4]),
                "后区1": int(nums[5]), "后区2": int(nums[6]),
                "前区和值": sum(int(x) for x in nums[:5]),
            })
        print(f"  大乐透 page {page}: 累计 {len(rows)}")
        if stop:
            break
        page += 1
        time.sleep(0.8)
    rows.sort(key=lambda r: r["开奖日期"])
    return rows


def fetch_ssq():
    rows, page = [], 1
    while True:
        url = ("https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?"
               + urllib.parse.urlencode({
                   "name": "ssq", "issueCount": "", "issueStart": "", "issueEnd": "",
                   "dayStart": START.isoformat(), "dayEnd": END.isoformat(),
                   "pageNo": page, "pageSize": 100, "week": "", "systemType": "PC"}))
        js = get(url, "https://www.cwl.gov.cn/")
        lst = js.get("result") or []
        if not lst:
            break
        stop = False
        for it in lst:
            d = date.fromisoformat(it["date"][:10])
            if d < START:
                stop = True
                continue
            if d > END:
                continue
            red = [int(x) for x in it["red"].split(",")]
            blue = int(it["blue"])
            rows.append({
                "期号": it["code"],
                "开奖日期": d.isoformat(),
                "红球1": red[0], "红球2": red[1], "红球3": red[2],
                "红球4": red[3], "红球5": red[4], "红球6": red[5],
                "蓝球": blue,
                "红球和值": sum(red),
            })
        print(f"  双色球 page {page}: 累计 {len(rows)}")
        if stop:
            break
        page += 1
        time.sleep(0.8)
    rows.sort(key=lambda r: r["开奖日期"])
    return rows


if __name__ == "__main__":
    dlt = fetch_dlt()
    print("大乐透总期数:", len(dlt), dlt[0]["期号"], "~", dlt[-1]["期号"])
    ssq = fetch_ssq()
    print("双色球总期数:", len(ssq), ssq[0]["期号"], "~", ssq[-1]["期号"])
    with open(OUT + r"\dlt.json", "w", encoding="utf-8") as f:
        json.dump(dlt, f, ensure_ascii=False, indent=1)
    with open(OUT + r"\ssq.json", "w", encoding="utf-8") as f:
        json.dump(ssq, f, ensure_ascii=False, indent=1)
    print("saved")
