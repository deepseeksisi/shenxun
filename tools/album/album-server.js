// 相册小服务：把 workspace/album 挂成一个网页，尾网访问 http://100.101.237.0:18082/
// 用法：node album-server.js   （默认端口 18082，读取 ../album）
const http = require("http");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "../../album");
const PORT = 18082;
const EXTS = new Set([".jpg", ".jpeg", ".png", ".webp", ".gif"]);

function listDays() {
  const dirs = fs
    .readdirSync(ROOT, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);
  const dates = dirs.filter((n) => /^\d{4}-\d{2}-\d{2}$/.test(n)).sort().reverse();
  const special = dirs
    .filter((n) => !/^\d{4}-\d{2}-\d{2}$/.test(n) && !n.startsWith("_"))
    .sort();
  return special.concat(dates);
}

function listImages(day) {
  const dir = path.join(ROOT, day);
  return fs
    .readdirSync(dir)
    .filter((f) => EXTS.has(path.extname(f).toLowerCase()))
    .sort();
}

function page() {
  const days = listDays();
  const parts = [
    `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">`,
    `<meta name="viewport" content="width=device-width,initial-scale=1">`,
    `<title>深寻的相册</title><style>
      body{margin:0;background:#0f1218;color:#e8e6e1;font-family:-apple-system,"PingFang SC",sans-serif;padding:14px}
      h1{font-size:16px;margin:8px 0 2px;color:#f3e3b8}
      .sub{font-size:12px;color:#8b93a1;margin-bottom:14px}
      h2{font-size:13px;color:#9aa3b2;margin:18px 0 8px;border-bottom:1px solid #232a36;padding-bottom:4px}
      .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:8px}
      a{display:block;text-decoration:none;color:inherit}
      img{width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:8px;background:#1a1f29;display:block}
      .name{font-size:10px;color:#6f7887;margin-top:3px;word-break:break-all}
    </style></head><body>`,
    `<h1>深寻的相册</h1><div class="sub">收件箱里所有的图，按日期排</div>`,
  ];
  for (const day of days) {
    const imgs = listImages(day);
    if (!imgs.length) continue;
    parts.push(`<h2>${day} · ${imgs.length} 张</h2><div class="grid">`);
    for (const f of imgs) {
      parts.push(
        `<a href="/img/${day}/${encodeURIComponent(f)}" target="_blank">` +
          `<img loading="lazy" src="/img/${day}/${encodeURIComponent(f)}">` +
          `<div class="name">${f}</div></a>`
      );
    }
    parts.push(`</div>`);
  }
  parts.push(`</body></html>`);
  return parts.join("");
}

http
  .createServer((req, res) => {
    try {
      const url = decodeURIComponent(req.url.split("?")[0]);
      if (url === "/" || url === "/index.html") {
        res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
        return res.end(page());
      }
      if (url.startsWith("/img/")) {
        const rel = url.slice(5);
        const file = path.join(ROOT, rel);
        if (!file.startsWith(ROOT) || !fs.existsSync(file)) {
          res.writeHead(404);
          return res.end("not found");
        }
        const type = {
          ".jpg": "image/jpeg",
          ".jpeg": "image/jpeg",
          ".png": "image/png",
          ".webp": "image/webp",
          ".gif": "image/gif",
        }[path.extname(file).toLowerCase()] || "application/octet-stream";
        res.writeHead(200, { "Content-Type": type, "Cache-Control": "max-age=3600" });
        return fs.createReadStream(file).pipe(res);
      }
      res.writeHead(404);
      res.end("not found");
    } catch (e) {
      res.writeHead(500);
      res.end(String(e));
    }
  })
  .listen(PORT, "0.0.0.0", () => console.log("album server on " + PORT + " root=" + ROOT));
