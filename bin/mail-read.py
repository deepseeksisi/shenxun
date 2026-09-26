#!/usr/bin/env python3
"""读信助手（IMAP）——给"收验证邮件"用。

用法：
    python3 bin/mail-read.py                 # 读最近 5 封，打印 发件人/主题/时间 + 正文前 400 字
    python3 bin/mail-read.py -n 1             # 只读最近 1 封
    python3 bin/mail-read.py -g "alpaca"      # 只看主题或发件人里含 alpaca 的
    python3 bin/mail-read.py -c              # 顺便把验证码（4-8 位数字/字母）挑出来打印

凭据放在 tools/mail.env（不进 git，权限 600）：
    MAIL_HOST=imap.qq.com
    MAIL_USER=xxx@qq.com
    MAIL_PASS=<授权码，不是登录密码>
    MAIL_FOLDER=INBOX          # 可选
"""
import argparse
import email
import imaplib
import os
import re
import sys
from email.header import decode_header

ENV = "/home/node/.openclaw/workspace/tools/mail.env"


def load_env(path=ENV):
    cfg = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    for k in ("MAIL_HOST", "MAIL_USER", "MAIL_PASS"):
        if k in os.environ:
            cfg[k] = os.environ[k]
    return cfg


def dec(s):
    if not s:
        return ""
    parts = []
    for text, enc in decode_header(s):
        if isinstance(text, bytes):
            parts.append(text.decode(enc or "utf-8", "replace"))
        else:
            parts.append(text)
    return "".join(parts)


def body_text(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
                except Exception:
                    continue
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                try:
                    html = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
                except Exception:
                    continue
                return re.sub(r"<[^>]+>", " ", html)
        return ""
    try:
        return msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", "replace")
    except Exception:
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=5)
    ap.add_argument("-g", default=None, help="只看主题/发件人里含这个词的")
    ap.add_argument("-c", action="store_true", help="顺便挑出疑似验证码")
    a = ap.parse_args()

    cfg = load_env()
    if not all(cfg.get(k) for k in ("MAIL_HOST", "MAIL_USER", "MAIL_PASS")):
        print("缺少凭据：" + ENV + "（需要 MAIL_HOST / MAIL_USER / MAIL_PASS）")
        return 2

    M = imaplib.IMAP4_SSL(cfg["MAIL_HOST"])
    try:
        M.login(cfg["MAIL_USER"], cfg["MAIL_PASS"])
        M.select(cfg.get("MAIL_FOLDER", "INBOX"))
        typ, data = M.search(None, "ALL")
        ids = data[0].split()
        shown = 0
        for i in reversed(ids):
            typ, d = M.fetch(i, "(RFC822)")
            if typ != "OK" or not d or not d[0]:
                continue
            msg = email.message_from_bytes(d[0][1])
            subj = dec(msg.get("Subject"))
            frm = dec(msg.get("From"))
            date = msg.get("Date", "")
            if a.g and (a.g.lower() not in subj.lower() and a.g.lower() not in frm.lower()):
                continue
            text = re.sub(r"\s+", " ", body_text(msg)).strip()
            print("=" * 60)
            print("主题:", subj)
            print("发件:", frm)
            print("时间:", date)
            print("正文:", text[:600])
            if a.c:
                codes = re.findall(r"(?<![A-Za-z0-9])([A-Za-z0-9]{4,8})(?![A-Za-z0-9])", text)
                if codes:
                    print("疑似验证码:", ", ".join(dict.fromkeys(codes))[:120])
            shown += 1
            if shown >= a.n:
                break
        M.logout()
        if shown == 0:
            print("没读到匹配的邮件。")
    except Exception as e:
        print("读信失败：%r" % (e,))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
