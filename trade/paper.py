#!/usr/bin/env python3
"""我自己的纸面账户（第一版）。

规则（写死，不临时改）：
- 初始虚拟资金 ¥100,000。
- 标的：trade/data/*.csv 里每一只，等权分仓。
- 策略：20 日均线。收盘价在均线上 → 持仓；跌破 → 空仓（第二天按收盘价换）。
- 费用：单边万分之三（ETF 无印花税）。
- 每个交易日只动一次，按当日收盘价成交。
- 账本：trade/state.json；每个动作追加一行到 trade/LOG.md。

用法：python3 trade/paper.py            # 按最新数据跑一遍
      python3 trade/paper.py --reset    # 清账重来
"""
import argparse
import csv
import glob
import json
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
STATE = os.path.join(HERE, "state.json")
LOG = os.path.join(HERE, "LOG.md")

INIT_CASH = 100000.0
FEE = 0.0003
MA_N = 20


def load_series():
    out = {}
    for path in sorted(glob.glob(os.path.join(DATA, "*.csv"))):
        code = os.path.splitext(os.path.basename(path))[0]
        rows = []
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows.append((r["date"], float(r["close"])))
        if len(rows) >= MA_N + 1:
            out[code] = rows
    return out


def load_state():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    return {"cash": INIT_CASH, "positions": {}, "equity": [], "last_date": None}


def save_state(s):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)


def append_log(lines):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    a = ap.parse_args()

    series = load_series()
    if not series:
        print("没有数据，先跑 python3 trade/fetch.py")
        return

    # 用所有标的中最新的那个交易日
    dates = {code: rows[-1][0] for code, rows in series.items()}
    today = max(dates.values())

    if a.reset or not os.path.exists(STATE):
        st = {"cash": INIT_CASH, "positions": {}, "equity": [], "last_date": None}
        fresh = True
    else:
        st = load_state()
        fresh = False

    if st.get("last_date") == today:
        print(f"{today} 已经跑过了，不重复动。")
        return

    log = [f"\n## {today}"]
    codes = sorted(series.keys())
    slot = INIT_CASH / len(codes)  # 每只的额定仓位

    for code in codes:
        rows = series[code]
        closes = [c for _d, c in rows]
        ma = sum(closes[-MA_N:]) / MA_N
        price = closes[-1]
        prev = closes[-2]
        ma_prev = sum(closes[-MA_N - 1 : -1]) / MA_N
        held = st["positions"].get(code, 0)

        want_in = price > ma
        was_in = prev > ma_prev
        st["positions"].setdefault(code, 0)

        # 头一回跑：按当下信号对齐仓位（不装“刚好抓到信号”）
        if fresh:
            was_in = not want_in

        if want_in and not was_in:
            budget = min(st["cash"], slot - st["positions"][code] * price)
            if budget > price:
                shares = int(budget / price)
                cost = shares * price * (1 + FEE)
                if shares > 0 and cost <= st["cash"]:
                    st["cash"] -= cost
                    st["positions"][code] += shares
                    log.append(
                        f"- **买入** {code} {shares} 股 @ {price:.3f}（{MA_N}日均线 {ma:.3f}，上穿）"
                    )
        elif (not want_in) and was_in and st["positions"][code] > 0:
            shares = st["positions"][code]
            proceeds = shares * price * (1 - FEE)
            st["cash"] += proceeds
            st["positions"][code] = 0
            log.append(f"- **卖出** {code} {shares} 股 @ {price:.3f}（{MA_N}日均线 {ma:.3f}，下破）")

    # 结算
    equity = st["cash"]
    detail = []
    for code in codes:
        sh = st["positions"].get(code, 0)
        if sh:
            px = series[code][-1][1]
            equity += sh * px
            detail.append(f"{code} {sh}股×{px:.3f}")
    st["equity"].append([today, round(equity, 2)])
    st["last_date"] = today

    ret = (equity / INIT_CASH - 1) * 100
    log.append(f"- 结算：现金 {st['cash']:.2f}｜市值 {equity - st['cash']:.2f}｜总权益 **{equity:.2f}**（{ret:+.2f}%）")
    if detail:
        log.append("- 持仓：" + "，".join(detail))
    append_log(log)
    save_state(st)

    print(f"{today} 跑完：权益 {equity:.2f}（{ret:+.2f}%），现金 {st['cash']:.2f}")
    for line in log[1:]:
        print("  " + line)


if __name__ == "__main__":
    main()
