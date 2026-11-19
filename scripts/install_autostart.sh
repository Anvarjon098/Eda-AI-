#!/usr/bin/env bash
# Eda AI'ni QuizBot kabi avtomatik ishga tushadigan qiladi:
#  - serverga SSH orqali kirganda bot ishlamayotgan bo'lsa, o'zi yonadi (.bashrc / .profile);
#  - cron bo'lsa, konteyner qayta yonganda va har 5 daqiqada tekshiriladi.
# Bir necha marta ishga tushirilsa ham qatorlar takrorlanmaydi.
START="$HOME/eda-ai/scripts/start.sh"
LINE='[ -x "$HOME/eda-ai/scripts/start.sh" ] && "$HOME/eda-ai/scripts/start.sh" >/dev/null 2>&1 </dev/null'

for rc in "$HOME/.bashrc" "$HOME/.profile"; do
    if grep -q "eda-ai/scripts/start.sh" "$rc" 2>/dev/null; then
        echo "✔ $rc — allaqachon qo'shilgan"
    else
        printf '\n# Eda AI to%sxtagan bo%slsa, ulanganda avtomatik ishga tushadi\n%s\n' "'" "'" "$LINE" >> "$rc"
        echo "✅ $rc ga qo'shildi"
    fi
done

if command -v crontab >/dev/null 2>&1; then
    ( crontab -l 2>/dev/null | grep -v "eda-ai/scripts/start.sh"
      echo "@reboot bash $START >/dev/null 2>&1"
      echo "*/5 * * * * bash $START >/dev/null 2>&1" ) | crontab - && echo "✅ cron: qayta yonganda va har 5 daqiqada tekshiriladi"
else
    echo "ℹ️ cron yo'q — bot konteyner qayta yongach, birinchi SSH ulanishda ishga tushadi"
fi

bash "$START"
