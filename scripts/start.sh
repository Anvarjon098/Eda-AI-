#!/usr/bin/env bash
# Botni fonda ishga tushiradi. Terminal yopilsa ham ishlayveradi,
# xato bilan to'xtasa 5 soniyadan keyin o'zi qayta ishga tushadi.
cd "$(dirname "$0")/.." || exit 1

if [ -f bot.pid ] && kill -0 "$(cat bot.pid)" 2>/dev/null; then
    echo "Bot allaqachon ishlayapti (PID $(cat bot.pid)). Qayta ishga tushirish: scripts/restart.sh"
    exit 0
fi

if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python3; fi

nohup setsid bash -c '
    while true; do
        "$0" -m bot >> bot.log 2>&1
        echo "$(date "+%F %T") bot to'"'"'xtadi, 5 soniyadan keyin qayta ishga tushadi" >> bot.log
        # log 5 MB dan oshsa, eskisini o'"'"'chiramiz (disk kichik)
        [ "$(stat -c %s bot.log 2>/dev/null || echo 0)" -gt 5242880 ] && mv bot.log bot.log.old
        sleep 5
    done
' "$PY" > /dev/null 2>&1 < /dev/null &
echo $! > bot.pid
sleep 3
if kill -0 "$(cat bot.pid)" 2>/dev/null; then
    echo "✅ Bot fonda ishga tushdi (PID $(cat bot.pid)). Loglar: scripts/logs.sh"
    tail -n 5 bot.log 2>/dev/null
else
    echo "❌ Bot ishga tushmadi. Loglar:"; tail -n 20 bot.log
fi
