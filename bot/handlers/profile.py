from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from .. import keyboards as kb
from ..calc import ACTIVITY_LEVELS, AGE_RANGE, HEIGHT_RANGE, WEIGHT_RANGE, daily_needs, parse_number
from ..db import Database, Profile
from ..states import ProfileForm
from ..views import HELP_TEXT, needs_text

router = Router(name="profile")


async def start_form(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ProfileForm.sex)
    await message.answer(
        "Kunlik kaloriya me'yoringizni hisoblash uchun bir nechta savol beraman.\n\n"
        "1/5. Jinsingizni tanlang:",
        reply_markup=kb.sex_kb(),
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db: Database) -> None:
    profile = await db.get_profile(message.from_user.id)
    if profile:
        await state.clear()
        await message.answer(
            f"Xush kelibsiz! 👋 Kunlik me'yoringiz: <b>{profile.daily_kcal}</b> kkal.\n\n"
            "Ovqat rasmini yuboring — kaloriyasini hisoblab beraman 📸",
            reply_markup=kb.main_menu(),
        )
        return
    await message.answer(
        "Assalomu alaykum! 👋 Men <b>Eda AI</b> — kaloriya hisoblovchi yordamchingizman.\n\n"
        "📸 Ovqatingizni rasmga olib yuborsangiz, AI uning kaloriyasini hisoblab beradi.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await start_form(message, state)


@router.message(Command("yangilash"))
async def cmd_update(message: Message, state: FSMContext) -> None:
    await start_form(message, state)


@router.callback_query(F.data == "profile:edit")
async def cb_edit(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await start_form(call.message, state)


@router.message(Command("cancel", "bekor"), StateFilter(ProfileForm))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=kb.main_menu())


@router.message(StateFilter(ProfileForm), F.photo | F.document)
async def photo_during_form(message: Message) -> None:
    await message.answer("Avval savollarga javob berib, profilni to'ldiring. Bekor qilish: /cancel")


@router.callback_query(ProfileForm.sex, F.data.startswith("sex:"))
async def cb_sex(call: CallbackQuery, state: FSMContext) -> None:
    sex = call.data.split(":", 1)[1]
    if sex not in ("male", "female"):
        await call.answer()
        return
    await state.update_data(sex=sex)
    await state.set_state(ProfileForm.age)
    await call.answer()
    await call.message.edit_text(f"1/5. Jins: {'👨 Erkak' if sex == 'male' else '👩 Ayol'}")
    await call.message.answer("2/5. Yoshingiz nechada? (masalan: <code>25</code>)")


@router.message(ProfileForm.sex)
async def sex_text(message: Message) -> None:
    await message.answer("Iltimos, quyidagi tugmalardan birini tanlang:", reply_markup=kb.sex_kb())


@router.message(ProfileForm.age, F.text)
async def got_age(message: Message, state: FSMContext) -> None:
    value = parse_number(message.text, *AGE_RANGE)
    if value is None or not value.is_integer():
        await message.answer(f"Yoshni butun son bilan kiriting ({AGE_RANGE[0]}–{AGE_RANGE[1]}). Masalan: <code>25</code>")
        return
    await state.update_data(age=int(value))
    await state.set_state(ProfileForm.height)
    await message.answer("3/5. Bo'yingiz necha santimetr? (masalan: <code>175</code>)")


@router.message(ProfileForm.height, F.text)
async def got_height(message: Message, state: FSMContext) -> None:
    value = parse_number(message.text, *HEIGHT_RANGE)
    if value is None:
        await message.answer(
            f"Bo'yni santimetrda kiriting ({HEIGHT_RANGE[0]}–{HEIGHT_RANGE[1]}). Masalan: <code>175</code>"
        )
        return
    await state.update_data(height_cm=value)
    await state.set_state(ProfileForm.weight)
    await message.answer("4/5. Vazningiz necha kilogramm? (masalan: <code>70</code> yoki <code>70.5</code>)")


@router.message(ProfileForm.weight, F.text)
async def got_weight(message: Message, state: FSMContext) -> None:
    value = parse_number(message.text, *WEIGHT_RANGE)
    if value is None:
        await message.answer(
            f"Vaznni kilogrammda kiriting ({WEIGHT_RANGE[0]}–{WEIGHT_RANGE[1]}). Masalan: <code>70</code>"
        )
        return
    await state.update_data(weight_kg=value)
    await state.set_state(ProfileForm.activity)
    await message.answer("5/5. Jismoniy faolligingiz qanday?", reply_markup=kb.activity_kb())


@router.message(ProfileForm.activity)
async def activity_text(message: Message) -> None:
    await message.answer("Iltimos, quyidagi tugmalardan birini tanlang:", reply_markup=kb.activity_kb())


@router.message(StateFilter(ProfileForm.age, ProfileForm.height, ProfileForm.weight))
async def need_text(message: Message) -> None:
    await message.answer("Iltimos, javobni son bilan yozing. Bekor qilish: /cancel")


@router.callback_query(ProfileForm.activity, F.data.startswith("act:"))
async def cb_activity(call: CallbackQuery, state: FSMContext, db: Database) -> None:
    activity = call.data.split(":", 1)[1]
    if activity not in ACTIVITY_LEVELS:
        await call.answer()
        return
    data = await state.get_data()
    await state.clear()
    await call.answer()
    n = daily_needs(data["sex"], data["age"], data["height_cm"], data["weight_kg"], activity)
    profile = Profile(
        user_id=call.from_user.id, sex=data["sex"], age=data["age"], height_cm=data["height_cm"],
        weight_kg=data["weight_kg"], activity=activity, daily_kcal=n.tdee,
    )
    await db.save_profile(profile)
    await call.message.edit_text(f"5/5. Faollik: {ACTIVITY_LEVELS[activity][1]}")
    await call.message.answer(needs_text(profile, n), reply_markup=kb.main_menu())


@router.message(Command("profil"))
@router.message(F.text == kb.BTN_PROFILE)
async def cmd_profile(message: Message, db: Database) -> None:
    profile = await db.get_profile(message.from_user.id)
    if not profile:
        await message.answer("Siz hali ma'lumotlaringizni kiritmagansiz. /start bosing.")
        return
    n = daily_needs(profile.sex, profile.age, profile.height_cm, profile.weight_kg, profile.activity)
    text = needs_text(profile, n).rsplit("\n\n", 1)[0]  # oxirgi "rasm yuboring" qatorisiz
    await message.answer(text, reply_markup=kb.profile_kb())


@router.message(Command("help", "yordam"))
@router.message(F.text == kb.BTN_HELP)
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=kb.main_menu())
