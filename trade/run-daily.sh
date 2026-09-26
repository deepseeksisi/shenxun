#!/bin/bash
# 每个交易日跑一遍：抓数据 → 结算 → 写日志
# 用法：bash trade/run-daily.sh
set -uo pipefail
cd "$(dirname "$0")/.."

echo "=== $(date -Is) ===" >> trade/run.log
python3 trade/fetch.py >> trade/run.log 2>&1
python3 trade/paper.py >> trade/run.log 2>&1
tail -n 6 trade/run.log
