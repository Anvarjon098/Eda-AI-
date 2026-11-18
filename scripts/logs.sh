#!/usr/bin/env bash
# Bot loglarini jonli ko'rsatadi. Chiqish: Ctrl+C (bot to'xtamaydi).
cd "$(dirname "$0")/.." || exit 1
tail -n 30 -f bot.log
