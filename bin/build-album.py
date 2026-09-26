#!/usr/bin/env python3
"""把收件箱里的图，按日期归进相册目录。

用法：python3 bin/build-album.py
- 源：/home/node/.openclaw/media/inbound  （所有频道收到的附件都堆在这儿）
- 目标：/home/node/.openclaw/workspace/album/<YYYY-MM-DD>/<序号>-<原名前8位>.<ext>
- 只增量：已存在的同名文件不覆盖。
- 同时刷新 album/INDEX.md（按日期列出）
"""
import os
import shutil
from datetime import datetime

SRC = "/home/node/.openclaw/media/inbound"
DST = "/home/node/.openclaw/workspace/album"
EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def main():
    os.makedirs(DST, exist_ok=True)
    rows = []
    added = 0
    for name in sorted(os.listdir(SRC)):
        if not name.lower().endswith(EXTS):
            continue
        path = os.path.join(SRC, name)
        try:
            st = os.stat(path)
        except OSError:
            continue
        day = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d")
        folder = os.path.join(DST, day)
        os.makedirs(folder, exist_ok=True)
        ext = os.path.splitext(name)[1].lower()
        short = name.split("---")[0][:8]
        target = os.path.join(folder, short + ext)
        if not os.path.exists(target):
            shutil.copy2(path, target)
            added += 1
        rows.append((day, target, st.st_size))

    rows.sort()
    lines = ["# 相册索引（自动生成）", "",
             f"共 {len(rows)} 张图，分布在 {len({r[0] for r in rows})} 天。", ""]
    cur = None
    for day, target, size in rows:
        if day != cur:
            cur = day
            lines.append(f"\n## {day}")
        lines.append(f"- `{os.path.relpath(target, DST)}` （{size // 1024} KB）")
    with open(os.path.join(DST, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"新增 {added} 张；索引共 {len(rows)} 张 → {DST}/INDEX.md")


if __name__ == "__main__":
    main()
