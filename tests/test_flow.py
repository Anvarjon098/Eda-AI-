"""Dispatcher orqali to'liq stsenariy: profil kiritish -> rasm yuborish -> bugungi hisob."""
import json
from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.base import BaseSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import AnswerCallbackQuery, EditMessageText, SendMessage, TelegramMethod
from aiogram.types import CallbackQuery, Chat, Message, PhotoSize, Update, User

from bot.ai import FoodAnalyzer
from bot.db import Database
from bot.handlers import routers

TZ = ZoneInfo("Asia/Tashkent")
USER = User(id=42, is_bot=False, first_name="Test")
CHAT = Chat(id=42, type="private")


class FakeSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.sent: list[TelegramMethod] = []

    async def make_request(self, bot, method, timeout=None):
        self.sent.append(method)
        if isinstance(method, (SendMessage, EditMessageText)):
            return Message(message_id=len(self.sent), date=datetime.now(), chat=CHAT,
                           text=method.text, from_user=User(id=1, is_bot=True, first_name="Bot")).as_(bot)
        return True

    async def stream_content(self, *a, **k):
        yield b""

    async def close(self):
        pass

    def texts(self):
        return [m.text for m in self.sent if isinstance(m, (SendMessage, EditMessageText))]


class StubAnalyzer:
    def __init__(self):
        self.calls = []

    async def analyze(self, image, media_type="image/jpeg", caption=None):
        from bot.ai import parse_analysis
        self.calls.append((image, media_type, caption))
        return parse_analysis(json.dumps({
            "is_food": True, "title": "Osh",
            "items": [{"name": "Osh", "portion_g": 350, "kcal": 650, "protein_g": 20, "fat_g": 28, "carbs_g": 75}],
            "total_kcal": 650, "total_protein_g": 20, "total_fat_g": 28, "total_carbs_g": 75,
            "confidence": "o'rtacha", "note": "Yog'li taom.",
        }))


@pytest.fixture
async def env(tmp_path):
    db = Database(str(tmp_path / "t.db"))
    await db.connect()
    session = FakeSession()
    bot = Bot("42:TEST", session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    async def fake_download(file, destination=None, **kw):
        destination.write(b"\xff\xd8fake")
        return destination
    bot.download = fake_download

    dp = Dispatcher(storage=MemoryStorage())
    analyzer = StubAnalyzer()
    dp["db"], dp["analyzer"], dp["tz"] = db, analyzer, TZ
    for r in routers:
        r._parent_router = None  # testlar orasida qayta ulash uchun
        dp.include_router(r)
    counter = iter(range(1, 10_000))

    async def text(t):
        msg = Message(message_id=next(counter), date=datetime.now(), chat=CHAT, from_user=USER, text=t)
        await dp.feed_update(bot, Update(update_id=next(counter), message=msg))

    async def click(data):
        msg = Message(message_id=next(counter), date=datetime.now(), chat=CHAT, text="q",
                      from_user=User(id=1, is_bot=True, first_name="Bot"))
        cb = CallbackQuery(id=str(next(counter)), from_user=USER, chat_instance="c", data=data, message=msg)
        await dp.feed_update(bot, Update(update_id=next(counter), callback_query=cb))

    async def photo(caption=None):
        ps = PhotoSize(file_id="f", file_unique_id="u", width=800, height=600, file_size=1000)
        msg = Message(message_id=next(counter), date=datetime.now(), chat=CHAT, from_user=USER,
                      photo=[ps], caption=caption)
        await dp.feed_update(bot, Update(update_id=next(counter), message=msg))

    yield SimpleNamespace(db=db, session=session, analyzer=analyzer, text=text, click=click, photo=photo)
    await db.close()


async def test_full_flow(env):
    await env.text("/start")
    assert "Jinsingizni" in env.session.texts()[-1]
    await env.click("sex:male")
    assert "Yoshingiz" in env.session.texts()[-1]
    await env.text("abc")
    assert "butun son" in env.session.texts()[-1]
    await env.text("25")
    await env.text("175")
    await env.text("70,5")
    assert "faolligingiz" in env.session.texts()[-1]
    await env.click("act:moderate")
    result = env.session.texts()[-1]
    assert "Vaznni saqlash uchun" in result

    profile = await env.db.get_profile(42)
    assert profile.weight_kg == 70.5 and profile.age == 25
    assert str(profile.daily_kcal) in result

    await env.photo("bitta porsiya")
    assert env.analyzer.calls[0][2] == "bitta porsiya"
    out = env.session.texts()[-1]
    assert "650 kkal" in out and f"Qoldi: <b>{profile.daily_kcal - 650}</b>" in out

    await env.text("/bugun")
    assert "1. Osh — 650 kkal" in env.session.texts()[-1]

    await env.click("meal:del:1")
    assert (await env.db.day_totals(42, datetime.now(TZ).date().isoformat())).kcal == 0


async def test_photo_without_profile(env):
    await env.photo()
    out = env.session.texts()[-1]
    assert "650 kkal" in out and "/start" in out


async def test_photo_during_form_is_rejected(env):
    await env.text("/start")
    await env.photo()
    assert "profilni to'ldiring" in env.session.texts()[-1]
    assert env.analyzer.calls == []
