#!/usr/bin/env python3
"""发信助手（SMTP，QQ 邮箱）。

用法：
    python3 bin/mail-send.py -t someone@example.com -s "主题" -b "正文"
    python3 bin/mail-send.py -t someone@example.com -s "主题" -f 正文.txt

凭据同样读 tools/mail.env（MAIL_USER / MAIL_PASS，QQ 那串授权码两用：IMAP + SMTP）。
"""
import argparse
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.header import Header

ENV = "/home/node/.openclaw/workspace/tools/mail.env"
SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465


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
    for k in ("MAIL_USER", "MAIL_PASS"):
        if k in os.environ:
            cfg[k] = os.environ[k]
    return cfg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--to", required=True)
    ap.add_argument("-s", "--subject", required=True)
    ap.add_argument("-b", "--body", default="")
    ap.add_argument("-f", "--file", default=None)
    a = ap.parse_args()

    cfg = load_env()
    if not cfg.get("MAIL_USER") or not cfg.get("MAIL_PASS"):
        print("缺少凭据，检查 " + ENV)
        return 2

    body = a.body
    if a.file:
        with open(a.file, encoding="utf-8") as f:
            body = f.read()

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(a.subject, "utf-8")
    msg["From"] = cfg["MAIL_USER"]
    msg["To"] = a.to

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=30) as s:
        s.login(cfg["MAIL_USER"], cfg["MAIL_PASS"])
        s.sendmail(cfg["MAIL_USER"], [a.to], msg.as_string())
    print(f"发出去了：{cfg['MAIL_USER']} → {a.to}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
