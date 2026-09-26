#!/usr/bin/env python3
"""抓日线数据（东方财富公开接口），存到 trade/data/<code>.csv

用法：python3 trade/fetch.py            # 抓默认那几只
      python3 trade/fetch.py 1.510300 0.159915
secid 格式：沪市 1.xxxxxx，深市 0.xxxxxx
"""
import csv
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
DEFAULT = ["1.510300", "1.510500"]  # 沪深300ETF、中证500ETF


def fetch(secid, lmt=180):
    url = (
        "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        f"?secid={secid}&fields1=f1,f2,f3,f4,f5&fields2=f51,f52,f53,f54,f55,f56,f57"
        f"&klt=101&fqt=1&end=20500101&lmt={lmt}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.loads(r.read().decode("utf-8", "replace"))
    data = d.get("data") or {}
    code = data.get("code")
    name = data.get("name")
    rows = []
    for line in data.get("klines") or []:
        p = line.split(",")
        # 日期,开,收,高,低,成交量,成交额
        rows.append([p[0], p[1], p[2], p[3], p[4], p[5], p[6]])
    return code, name, rows


def main():
    os.makedirs(DATA, exist_ok=True)
    secids = sys.argv[1:] or DEFAULT
    for secid in secids:
        try:
            code, name, rows = fetch(secid)
        except Exception as e:
            print(f"{secid}: 抓取失败 {e!r}")
            continue
        path = os.path.join(DATA, f"{code}.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date", "open", "close", "high", "low", "volume", "amount"])
            w.writerows(rows)
        print(f"{code} {name}: {len(rows)} 根，最新 {rows[-1][0]} 收 {rows[-1][2]} → {path}")


if __name__ == "__main__":
    main()
