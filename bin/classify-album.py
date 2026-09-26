#!/usr/bin/env python3
"""给相册里的图分个类（粗筛）：屏幕截图 vs 照片。

判据：长宽比。手机截图都是"细长条"（宽高比 ≥ 1.8），相机拍的照片多是 4:3（≈1.33）。
输出：album/TAGS.md（分组清单），并把"照片"候选拷到 album/_候选照片/ 方便我一张张读。
"""
import os
import shutil
import struct
from collections import defaultdict

ALBUM = "/home/node/.openclaw/workspace/album"
OUT = os.path.join(ALBUM, "_候选照片")


def jpeg_size(p):
    with open(p, "rb") as f:
        d = f.read()
    i = 2
    while i < len(d) - 9:
        if d[i] != 0xFF:
            i += 1
            continue
        m = d[i + 1]
        if m in (0xC0, 0xC1, 0xC2, 0xC3):
            h, w = struct.unpack(">HH", d[i + 5 : i + 9])
            return w, h
        if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        ln = struct.unpack(">H", d[i + 2 : i + 4])[0]
        i += 2 + ln
    return None


def png_size(p):
    with open(p, "rb") as f:
        d = f.read(33)
    if len(d) < 24:
        return None
    w, h = struct.unpack(">II", d[16:24])
    return w, h


def size(p):
    e = os.path.splitext(p)[1].lower()
    try:
        if e in (".jpg", ".jpeg"):
            return jpeg_size(p)
        if e == ".png":
            return png_size(p)
    except Exception:
        return None
    return None


def main():
    os.makedirs(OUT, exist_ok=True)
    screen, photo, unknown = [], [], []
    for root, _dirs, files in os.walk(ALBUM):
        if "_候选照片" in root:
            continue
        for f in sorted(files):
            if os.path.splitext(f)[1].lower() not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
                continue
            p = os.path.join(root, f)
            s = size(p)
            rel = os.path.relpath(p, ALBUM)
            if not s:
                unknown.append(rel)
                continue
            w, h = s
            ratio = max(w, h) / max(1, min(w, h))
            (screen if ratio >= 1.75 else photo).append((rel, s))

    for rel, s in photo:
        tgt = os.path.join(OUT, os.path.basename(rel))
        if not os.path.exists(tgt):
            shutil.copy2(os.path.join(ALBUM, rel), tgt)

    lines = ["# 相册分类（粗筛，按长宽比）", "",
             f"- 屏幕类（细长条 ≥1.75）：{len(screen)} 张",
             f"- 照片类（接近 4:3）：{len(photo)} 张 → 已拷到 `album/_候选照片/`",
             f"- 尺寸读不出（webp 等）：{len(unknown)} 张", ""]
    lines.append("\n## 照片类（我要一张张读的）")
    for rel, s in photo:
        lines.append(f"- `{rel}` {s[0]}x{s[1]}")
    lines.append("\n## 屏幕类")
    for rel, s in screen:
        lines.append(f"- `{rel}` {s[0]}x{s[1]}")
    if unknown:
        lines.append("\n## 读不出尺寸")
        for rel in unknown:
            lines.append(f"- `{rel}`")
    with open(os.path.join(ALBUM, "TAGS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"屏幕 {len(screen)}｜照片 {len(photo)}｜未知 {len(unknown)} → album/TAGS.md")


if __name__ == "__main__":
    main()
