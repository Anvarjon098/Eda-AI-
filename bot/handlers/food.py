import io
from html import escape
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, F, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from .. import keyboards as kb
from ..ai import AnalysisError, FoodAnalyzer
from ..db import Database
from ..views import analysis_text, today_text

log = logging.getLogger(__name__)
router = Router(name="food")

MAX_IMAGE_BYTES = 5 * 1024 * 1024  # Claude API rasm chegarasi
IMAGE_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def today(tz: ZoneInfo) -> str:
    return datetime.now(tz).date().isoformat()


@router.message(F.photo | (F.document & F.document.mime_type.in_(IMAGE_MIME)))
async def on_photo(message: Message, bot: Bot, db: Database, analyzer: FoodAnalyzer, tz: ZoneInfo) -> None:
    if message.photo:
        file_id, size, mime = message.photo[-1].file_id, message.photo[-1].file_size, "image/jpeg"
    else:
        file_id, size, mime = message.document.file_id, message.document.file_size, message.document.mime_type
    if size and size > MAX_IMAGE_BYTES:
        await message.answer("Rasm juda katta (5 MB dan ortiq). Uni oddiy rasm sifatida yuboring.")
        return

    status = await message.answer("⏳ Rasm tahlil qilinmoqda...")
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    buf = io.BytesIO()
    await bot.download(file_id, destination=buf)
    image = buf.getvalue()
    if len(image) > MAX_IMAGE_BYTES:
        await status.edit_text("Rasm juda katta (5 MB dan ortiq). Uni oddiy rasm sifatida yuboring.")
        return

    try:
        result = await analyzer.analyze(image, mime, message.caption)
    except AnalysisError as e:
        await status.edit_text(f"😔 {e}")
        return

    if not result.is_food or result.total_kcal <= 0:
        await status.edit_text(
            "🤔 Rasmda ovqat topilmadi.\n" + (f"<i>{escape(result.note)}</i>\n" if result.note else "")
            + "\nOvqatni yaqinroqdan, yorug' joyda rasmga olib yuboring."
        )
        return

    user_id = message.from_user.id
    day = today(tz)
    meal_id = await db.add_meal(
        user_id, day, result.title, result.total_kcal,
        result.total_protein_g, result.total_fat_g, result.total_carbs_g,
    )
    profile = await db.get_profile(user_id)
    totals = await db.day_totals(user_id, day)
    await status.edit_text(
        analysis_text(result, totals, profile.daily_kcal if profile else None),
        reply_markup=kb.meal_kb(meal_id),
    )


@router.callback_query(F.data.startswith("meal:del:"))
async def cb_delete_meal(call: CallbackQuery, db: Database) -> None:
    try:
        meal_id = int(call.data.rsplit(":", 1)[1])
    except ValueError:
        await call.answer()
        return
    deleted = await db.delete_meal(call.from_user.id, meal_id)
    await call.answer("Hisobdan o'chirildi" if deleted else "Allaqachon o'chirilgan")
    if deleted and call.message:
        await call.message.edit_text(call.message.html_text + "\n\n<s>Hisobdan o'chirildi</s>")


@router.message(Command("bugun"))
@router.message(F.text == kb.BTN_TODAY)
async def cmd_today(message: Message, db: Database, tz: ZoneInfo) -> None:
    user_id = message.from_user.id
    day = today(tz)
    profile = await db.get_profile(user_id)
    totals = await db.day_totals(user_id, day)
    meals = await db.day_meals(user_id, day)
    await message.answer(today_text(totals, meals, profile.daily_kcal if profile else None))


@router.message()
async def fallback(message: Message) -> None:
    await message.answer(
        "📸 Ovqat rasmini yuboring — kaloriyasini hisoblab beraman.\n/help — yordam",
        reply_markup=kb.main_menu(),
    )
