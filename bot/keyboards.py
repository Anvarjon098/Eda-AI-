from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from .calc import ACTIVITY_LEVELS

BTN_TODAY = "📊 Bugun"
BTN_PROFILE = "👤 Profil"
BTN_HELP = "ℹ️ Yordam"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_TODAY), KeyboardButton(text=BTN_PROFILE)],
                  [KeyboardButton(text=BTN_HELP)]],
        resize_keyboard=True,
        input_field_placeholder="Ovqat rasmini yuboring 📸",
    )


def sex_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="👨 Erkak", callback_data="sex:male"),
        InlineKeyboardButton(text="👩 Ayol", callback_data="sex:female"),
    ]])


def activity_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=f"act:{key}")]
        for key, (_, label) in ACTIVITY_LEVELS.items()
    ])


def profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✏️ Ma'lumotlarni yangilash", callback_data="profile:edit"),
    ]])


def meal_kb(meal_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🗑 Hisobdan o'chirish", callback_data=f"meal:del:{meal_id}"),
    ]])
