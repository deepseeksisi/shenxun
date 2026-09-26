@echo off
cd /d C:\Users\shenxun\deepseeksisi-memory
echo [bat] start %date% %time% >> lol-bat.log
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\shenxun\deepseeksisi-memory\lol-say-agent.ps1" >> lol-bat.log 2>&1
echo [bat] end %date% %time% >> lol-bat.log
echo.
echo 传话兵停了（上面这行是原因）。按任意键关闭。
pause >nul
