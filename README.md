# 🍽 Eda AI — kaloriya hisoblovchi Telegram bot

Foydalanuvchi o'z ma'lumotlarini kiritadi, bot uning **kunlik kaloriya sarfini** hisoblaydi.
Ovqat rasmini yuborganda esa **Claude AI** taomni aniqlab, kaloriya va oqsil/yog'/uglevod miqdorini hisoblaydi.

## Imkoniyatlar

- **Profil:** jins, yosh, bo'y (sm), vazn (kg) va jismoniy faollik so'raladi.
- **Kunlik me'yor:** Mifflin–St Jeor formulasi asosida hisoblanadi:
  - tinch holatdagi sarf (BMR);
  - vaznni saqlash, tashlash (−500 kkal) va olish (+400 kkal) uchun kunlik kaloriya;
  - TVI (BMI).
- **📸 Ovqat rasmi:** AI har bir taomni, uning porsiyasini (gramm) va kaloriyasini aniqlaydi. O'zbek taomlari (osh, somsa, lag'mon, manti va h.k.) hisobga olingan.
  - Rasmga izoh yozsangiz (masalan, *«2 porsiya»*), hisob aniqroq chiqadi.
  - Natija bugungi hisobga avtomatik qo'shiladi. «🗑 Hisobdan o'chirish» tugmasi bilan olib tashlash mumkin.
- **📊 /bugun:** bugun yeyilgan ovqatlar, jami kaloriya va me'yordan qancha qolgani.

## Buyruqlar

| Buyruq | Vazifasi |
|---|---|
| `/start` | Boshlash va profilni kiritish |
| `/bugun` | Bugungi hisob |
| `/profil` | Profil va kunlik me'yor |
| `/yangilash` | Yosh, bo'y, vaznni qayta kiritish |
| `/cancel` | Profil kiritishni bekor qilish |
| `/help` | Yordam |

## O'rnatish

1. Bot tokenini [@BotFather](https://t.me/BotFather) dan oling.
2. Claude API kalitini [platform.claude.com](https://platform.claude.com) dan oling.
3. Quyidagi buyruqlarni bajaring:

```bash
git clone https://github.com/Anvarjon098/Eda-AI-.git eda-ai
cd eda-ai
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
nano .env          # BOT_TOKEN va ANTHROPIC_API_KEY ni yozing
.venv/bin/python -m bot
```

### `.env` sozlamalari

| O'zgaruvchi | Tavsifi | Standart qiymat |
|---|---|---|
| `BOT_TOKEN` | Telegram bot tokeni | — (majburiy) |
| `ANTHROPIC_API_KEY` | Claude API kaliti | — (majburiy) |
| `CLAUDE_MODEL` | Rasmni tahlil qiladigan model | `claude-opus-5-5` |
| `DB_PATH` | SQLite baza fayli | `eda.db` |
| `TIMEZONE` | Kun qaysi vaqt mintaqasi bo'yicha hisoblanadi | `Asia/Tashkent` |

Xarajatni kamaytirish uchun `CLAUDE_MODEL=claude-sonnet-5-5` qilib qo'yish mumkin. Bu model arzonroq, lekin biroz kamroq aniq.

### Root huquqisiz serverda (fonda ishlatish)

`sudo` va `systemd` bo'lmagan serverlarda (masalan, bepul konteynerlarda) quyidagi skriptlardan foydalaning.
Bot terminal yopilganda ham ishlayveradi va xato bilan to'xtasa, o'zi qayta ishga tushadi.

| Buyruq | Vazifasi |
|---|---|
| `scripts/start.sh` | Botni fonda ishga tushirish |
| `scripts/stop.sh` | To'xtatish |
| `scripts/restart.sh` | GitHub'dan yangilab, qayta ishga tushirish |
| `scripts/logs.sh` | Loglarni ko'rish (chiqish uchun Ctrl+C bosiladi, bot to'xtamaydi) |

### Serverda (systemd)

```bash
sudo useradd -r -m -d /opt/eda-ai edaai
sudo -u edaai git clone https://github.com/Anvarjon098/Eda-AI-.git /opt/eda-ai
cd /opt/eda-ai && sudo -u edaai python3 -m venv .venv && sudo -u edaai .venv/bin/pip install -r requirements.txt
sudo -u edaai cp .env.example .env && sudo -u edaai nano .env
sudo cp deploy/eda-ai.service /etc/systemd/system/
sudo systemctl enable --now eda-ai
journalctl -u eda-ai -f     # loglarni ko'rish
```

## Testlar

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
```

## Tuzilma

```
bot/
  __main__.py        # ishga tushirish
  config.py          # .env sozlamalari
  calc.py            # BMR / kunlik kaloriya / TVI hisobi
  ai.py              # Claude orqali rasm tahlili (JSON javob)
  db.py              # SQLite: foydalanuvchilar va ovqatlar
  views.py           # xabar matnlari
  keyboards.py       # tugmalar
  states.py          # profil kiritish bosqichlari (FSM)
  handlers/
    profile.py       # /start, profil kiritish, /profil
    food.py          # rasm tahlili, /bugun
tests/               # pytest testlari
deploy/              # systemd xizmati
```

> ⚠️ Hisoblar taxminiy. Ular tibbiy maslahat o'rnini bosmaydi.
