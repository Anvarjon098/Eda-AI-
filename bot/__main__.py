import asyncio
import logging
import os
import ssl

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNotFound, TelegramUnauthorizedError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, ErrorEvent

from .ai import FoodAnalyzer
from .config import load_config
from .db import Database
from .handlers import routers

COMMANDS = [
    BotCommand(command="start", description="Boshlash"),
    BotCommand(command="bugun", description="Bugungi kaloriya hisobi"),
    BotCommand(command="profil", description="Profil va kunlik me'yor"),
    BotCommand(command="yangilash", description="Yosh, bo'y, vaznni yangilash"),
    BotCommand(command="help", description="Yordam"),
]


def make_session() -> AiohttpSession:
    """HTTPS_PROXY / SSL_CERT_FILE berilgan bo'lsa, ulardan foydalanadi."""
    proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    session = AiohttpSession(proxy=proxy) if proxy else AiohttpSession()
    cafile = os.getenv("SSL_CERT_FILE")
    if cafile:
        session._connector_init["ssl"] = ssl.create_default_context(cafile=cafile)
    return session


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = load_config()

    db = Database(config.db_path)
    await db.connect()

    bot = Bot(
        config.bot_token,
        session=make_session(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp["db"] = db
    dp["analyzer"] = FoodAnalyzer(config.anthropic_api_key, config.claude_model)
    dp["tz"] = config.timezone
    for r in routers:
        dp.include_router(r)

    @dp.errors()
    async def on_error(event: ErrorEvent) -> bool:
        logging.exception("Kutilmagan xato", exc_info=event.exception)
        msg = event.update.message or (event.update.callback_query and event.update.callback_query.message)
        if msg:
            try:
                await msg.answer("😔 Kutilmagan xatolik yuz berdi. Qayta urinib ko'ring.")
            except Exception:
                pass
        return True

    try:
        me = await bot.get_me()
    except (TelegramNotFound, TelegramUnauthorizedError):
        await db.close()
        await bot.session.close()
        raise SystemExit(
            "BOT_TOKEN noto'g'ri: Telegram uni tanimadi. @BotFather'dan tokenni to'liq "
            "(masalan 123456789:AA... ko'rinishida) qayta nusxalab, .env fayliga yozing."
        )
    logging.info("Bot ishga tushdi: @%s", me.username)
    await bot.set_my_commands(COMMANDS)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
