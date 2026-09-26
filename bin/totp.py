#!/usr/bin/env python3
"""算 TOTP 动态码（就是 GitHub/Google 那种 6 位码）。

用法：
    python3 bin/totp.py            # 读 tools/totp.env 里的 TOTP_SECRET
    python3 bin/totp.py <base32密钥>

原理：TOTP = HMAC-SHA1(密钥, 当前时间戳/30) 取 6 位。密钥（那串 base32）给到我，
我这边就能自己算，不需要手机。
"""
import base64
import hashlib
import hmac
import os
import struct
import sys
import time

ENV = "/home/node/.openclaw/workspace/tools/totp.env"


def load_secret():
    if os.path.exists(ENV):
        with open(ENV, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("TOTP_SECRET="):
                    return line.split("=", 1)[1].strip()
    return None


def totp(secret, at=None, digits=6, period=30):
    key = base64.b32decode(secret.upper().replace(" ", ""), casefold=True)
    counter = int((at if at is not None else time.time()) // period)
    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    off = h[-1] & 0x0F
    code = struct.unpack(">I", h[off : off + 4])[0] & 0x7FFFFFFF
    return str(code % (10**digits)).zfill(digits)


def main():
    secret = sys.argv[1] if len(sys.argv) > 1 else load_secret()
    if not secret:
        print("没有密钥：把它写进 " + ENV + "（TOTP_SECRET=xxxx）或直接命令行传参")
        return 2
    now = time.time()
    left = int(30 - now % 30)
    print(f"{totp(secret)}   （还剩 {left} 秒）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
