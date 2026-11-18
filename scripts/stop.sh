#!/usr/bin/env bash
# Fondagi botni to'xtatadi.
cd "$(dirname "$0")/.." || exit 1
if [ -f bot.pid ] && kill -0 "$(cat bot.pid)" 2>/dev/null; then
    # setsid tufayli butun guruhni (qayta ishga tushirish sikli + python) to'xtatamiz
    kill -- -"$(cat bot.pid)" 2>/dev/null || kill "$(cat bot.pid)"
    echo "🛑 Bot to'xtatildi."
else
    echo "Bot ishlamayapti."
fi
rm -f bot.pid
