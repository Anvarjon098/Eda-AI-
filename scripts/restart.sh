#!/usr/bin/env bash
# Kodni GitHub'dan yangilab, botni qayta ishga tushiradi.
cd "$(dirname "$0")/.." || exit 1
scripts/stop.sh
git pull --ff-only && { [ -x .venv/bin/pip ] && .venv/bin/pip install -q --no-cache-dir -r requirements.txt; }
scripts/start.sh
