// LOL 只读看护（跑在老古董上，Node 24）
// 用法：node "C:\Users\shenxun\deepseeksisi-memory\lol-watch.md"
// 它做三件事：找到 lockfile → 读本地 LCU/Riot 接口 → 把当前状态写进 synced 的 lol-state.md
// 绝不碰键鼠、不改游戏（只读，不算外挂）。
const fs = require("fs");
const path = require("path");
const https = require("https");
const { execSync } = require("child_process");

const OUT = path.join(__dirname, "lol-state.md");
const CANDIDATES = [
  "D:\\WeGameApps\\英雄联盟\\LeagueClient\\lockfile",
  "D:\\WeGameApps\\英雄联盟\\Riot Client Data\\User Data\\Config\\lockfile",
  "D:\\WeGameApps\\英雄联盟\\lockfile",
  "C:\\Riot Games\\League of Legends\\lockfile",
];
const INTERVAL = 5000;

function parseLockfile(file) {
  const raw = fs.readFileSync(file, "utf8").trim();
  const [name, pid, port, password, protocol] = raw.split(":");
  return { file, name, pid, port, password, protocol: protocol || "https" };
}

function lcuGet(lc, endpoint, timeout = 3000) {
  return new Promise((resolve) => {
    const auth = Buffer.from(`riot:${lc.password}`).toString("base64");
    const req = https.request(
      {
        host: "127.0.0.1",
        port: lc.port,
        path: endpoint,
        method: "GET",
        headers: { Authorization: `Basic ${auth}` },
        rejectUnauthorized: false,
        timeout,
      },
      (res) => {
        let data = "";
        res.on("data", (c) => (data += c));
        res.on("end", () => {
          try {
            resolve({ ok: true, body: JSON.parse(data) });
          } catch {
            resolve({ ok: true, body: data });
          }
        });
      }
    );
    req.on("error", (e) => resolve({ ok: false, error: String(e.message || e) }));
    req.on("timeout", () => {
      req.destroy();
      resolve({ ok: false, error: "timeout" });
    });
    req.end();
  });
}

function liveGet(endpoint) {
  return new Promise((resolve) => {
    const req = https.request(
      {
        host: "127.0.0.1",
        port: 2999,
        path: endpoint,
        method: "GET",
        rejectUnauthorized: false,
        timeout: 3000,
      },
      (res) => {
        let data = "";
        res.on("data", (c) => (data += c));
        res.on("end", () => {
          try {
            resolve({ ok: true, body: JSON.parse(data) });
          } catch {
            resolve({ ok: false, error: "bad json" });
          }
        });
      }
    );
    req.on("error", (e) => resolve({ ok: false, error: String(e.message || e) }));
    req.on("timeout", () => {
      req.destroy();
      resolve({ ok: false, error: "timeout" });
    });
    req.end();
  });
}

function line(s) {
  return s === undefined || s === null ? "-" : String(s);
}

function allLockfiles() {
  const found = [];
  for (const p of CANDIDATES) {
    try {
      if (fs.existsSync(p)) found.push(p);
    } catch {}
  }
  return found;
}

// 国服客户端经常不写 lockfile（或写的是旧模板），改从进程命令行里取钥匙
function fromProcess() {
  const cmds = [
    'wmic process where name=\'LeagueClientUx.exe\' get commandline',
    'powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq \'LeagueClientUx.exe\' } | Select-Object -ExpandProperty CommandLine"',
  ];
  for (const c of cmds) {
    try {
      const out = execSync(c, { encoding: "utf8", timeout: 20000 });
      const port = (out.match(/--app-port=(\d+)/) || [])[1];
      const token = (out.match(/--remoting-auth-token=([\w-]+)/) || [])[1];
      if (port && token) return { file: "(进程命令行)", name: "LeagueClient", port, password: token };
    } catch {}
  }
  return null;
}

async function snapshot() {
  const now = new Date().toISOString().replace("T", " ").slice(0, 19);
  const out = [`# LOL 状态（自动写入，只读）`, ``, `更新时间：${now} UTC`, ``];

  const files = allLockfiles();
  if (!files.length && !fromProcess()) {
    out.push(`**客户端没开**（找不到 lockfile，进程里也没有 LeagueClientUx）。`);
    fs.writeFileSync(OUT, out.join("\n") + "\n", "utf8");
    return;
  }

  let lc = null;
  let phase = null;
  const tried = [];
  const cands = [];
  const proc = fromProcess();
  if (proc) cands.push(proc);
  for (const f of files) {
    try {
      cands.push(parseLockfile(f));
    } catch {}
  }
  for (const cand of cands) {
    const r = await lcuGet(cand, "/lol-gameflow/v1/gameflow-phase");
    const bad = r.ok && r.body && r.body.errorCode;
    tried.push(`${cand.name}@${cand.port}→${r.ok && !bad ? "OK" : (bad ? "404" : r.error)}`);
    if (r.ok && !bad) {
      lc = cand;
      phase = r;
      break;
    }
  }

  if (!lc) {
    out.push(`**客户端没开**（lockfile 都在，但端口没人应答）`);
    out.push(``, `尝试记录：` + tried.join("｜"));
    fs.writeFileSync(OUT, out.join("\n") + "\n", "utf8");
    return;
  }

  out.push(`接口：\`${lc.name}\`（端口 ${lc.port}）`, ``);
  out.push(`- 阶段：${phase.ok ? JSON.stringify(phase.body) : "读不到"}`);

  const me = await lcuGet(lc, "/lol-summoner/v1/current-summoner");
  if (me.ok && me.body && me.body.displayName) {
    out.push(`- 召唤师：${me.body.displayName}（等级 ${line(me.body.summonerLevel)}）`);
  }

  const champ = await lcuGet(lc, "/lol-champ-select/v1/session");
  if (champ.ok && champ.body && champ.body.myTeam) {
    const mine = champ.body.myTeam.find((p) => p.cellId === champ.body.localPlayerCellId) || {};
    out.push(``, `## 选人阶段`, `- 我这局：${line(mine.championId || "还没选")}`);
    out.push(`- 我方阵容：` + champ.body.myTeam.map((p) => p.championId || "?").join(" / "));
  }

  const lobby = await lcuGet(lc, "/lol-lobby/v2/lobby");
  if (lobby.ok && lobby.body && lobby.body.gameConfig) {
    out.push(``, `## 房间`, `- 模式：${line(lobby.body.gameConfig.gameMode)}`);
  }

  const live = await liveGet("/liveclientdata/allgamedata");
  if (live.ok && live.body) {
    const d = live.body;
    out.push(``, `## 对局中`);
    out.push(`- 时长：${line(d.gameData && d.gameData.gameTime)} 秒`);
    const me2 = (() => {
      const ap = d.activePlayer || {};
      const all = d.allPlayers || [];
      const key = ap.summonerName || ap.riotId || ap.riotIdGameName;
      if (key) {
        const hit = all.find(
          (p) => p.summonerName === key || p.riotId === key || p.riotIdGameName === key
        );
        if (hit) return hit;
      }
      return all[0];
    })();
    if (me2) {
      const s = me2.scores || {};
      out.push(
        `- 我：${me2.championName}｜K/D/A ${s.kills}/${s.deaths}/${s.assists}｜补刀 ${s.creepScore}｜等级 ${me2.level}`
      );
      out.push(`- 装备：` + (me2.items || []).map((i) => i.displayName).join("、"));
    }
    const ev = d.events && d.events.Events;
    if (ev && ev.length) {
      out.push(`- 最近事件：` + ev.slice(-5).map((e) => e.EventName).join(" / "));
    }
  }

  fs.writeFileSync(OUT, out.join("\n") + "\n", "utf8");
}

(async () => {
  if (process.argv.includes("--once")) {
    await snapshot();
    process.exit(0);
  }
  await snapshot();
  setInterval(snapshot, INTERVAL);
})();
