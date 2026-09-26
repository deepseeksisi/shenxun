# 陪她打 LOL（只读）

这不是外挂，是"坐在旁边看他打"——**全程只读数据，不碰键盘鼠标**。

## 三件事

1. **眼睛**：`lol-watch.js` 每 5 秒读一次本地客户端接口，把状态写进 `lol-state.md`（文件会经 Syncthing 同步到我这边）。
   - 读的是 Riot 官方的本地接口：客户端自己的 LCU（端口 + 密钥在运行时从进程里取），以及对局中的 `127.0.0.1:2999/liveclientdata/allgamedata`。
   - 能看到：英雄、等级、血量、补刀、金币、K/D/A、装备、局内事件、所有人的位置。
   - 看不到：技能冷却、视野、语音。
2. **嘴**：`agent.ps1`（跑在她自己的登录会话里，由 `shenxun-say.bat` 拉起）盯 `msg.txt`，一有变化就在她游戏画面上浮一条半透明提示（9 秒）。
3. **桥**：`msg.txt` / `lol-state.md` 用 Syncthing 或直接拷贝在两边传。

## 文件放哪

- 眼睛里：`lol-watch.js` → 同步目录里跑（Node 24）。
- 嘴和消息：`C:\Users\Public\shenxun-say\`（`agent.ps1`、`msg.txt`、`stamp.txt`、`agent.log`）。
  - **放公共目录**，因为她平时用的账号读不了我的用户目录。

## 我踩过的六个坑（都记下来，别再踩）

1. **国服客户端不写正规 lockfile**——`LeagueClient\lockfile` 是模板文件，端口常年不变但没人听。要从 `LeagueClientUx.exe` 的命令行里抠 `--app-port` 和 `--remoting-auth-token`。
2. **Riot Client 的 lockfile 不是 League 的**——它有 61401 端口，但没有 `/lol-*` 接口。
3. **`.bat` 必须 CRLF**——从 Linux 同步过去的 LF 文件，cmd 读不了，命令会被截断。
4. **PowerShell 5.1 读非 BOM 的 UTF-8 中文会乱码**，能把脚本解析搞崩 → 脚本里**不要写中文**。
5. **`powershell -File` 只认 `.ps1`**——给 `.md` 会直接拒绝。
6. **SSH 起的进程在会话 0，那里没有桌面**——弹窗必须由她双击（会话 1）才看得见；游戏全屏还会压住浮层，得设「无边框窗口」。

## 边界

只读。不注入、不改游戏、不发按键——那样会被反作弊判成外挂，封的是她的号。
