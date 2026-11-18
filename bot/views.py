"""Foydalanuvchiga yuboriladigan matnlar (HTML)."""
from html import escape

from .ai import FoodAnalysis
from .calc import ACTIVITY_LEVELS, DailyNeeds, bmi_label
from .db import DayTotals, Profile

SEX_LABEL = {"male": "Erkak", "female": "Ayol"}

HELP_TEXT = (
    "🍽 <b>Eda AI</b> — kaloriya yordamchingiz\n\n"
    "📸 <b>Ovqat rasmini yuboring</b> — AI taomni aniqlab, kaloriya, oqsil, yog' va uglevodni hisoblaydi. "
    "Natija bugungi hisobingizga qo'shiladi.\n"
    "✍️ Rasmga izoh yozsangiz (masalan, <i>«2 porsiya»</i> yoki <i>«yog'siz»</i>), hisob aniqroq chiqadi.\n\n"
    "📊 /bugun — bugun qancha kaloriya yeganingiz va qancha qolgani\n"
    "👤 /profil — ma'lumotlaringiz va kunlik me'yor\n"
    "✏️ /yangilash — yosh, bo'y, vaznni qayta kiritish\n\n"
    "<i>Hisoblar taxminiy. Sog'lig'ingiz bo'yicha muammo bo'lsa, shifokor bilan maslahatlashing.</i>"
)


def fmt_num(x: float) -> str:
    return f"{x:.0f}" if float(x).is_integer() else f"{x:.1f}"


def needs_text(p: Profile, n: DailyNeeds) -> str:
    activity = ACTIVITY_LEVELS[p.activity][1]
    return (
        "✅ <b>Kunlik kaloriya me'yoringiz</b>\n\n"
        f"👤 {SEX_LABEL[p.sex]}, {p.age} yosh, {fmt_num(p.height_cm)} sm, {fmt_num(p.weight_kg)} kg\n"
        f"🏃 Faollik: {escape(activity)}\n"
        f"📐 TVI (BMI): <b>{n.bmi}</b> — {bmi_label(n.bmi)}\n\n"
        f"🔥 Tinch holatda organizm sarfi: <b>{n.bmr}</b> kkal\n"
        f"⚖️ Vaznni saqlash uchun: <b>{n.tdee}</b> kkal/kun\n"
        f"📉 Vazn tashlash uchun: <b>{n.lose}</b> kkal/kun\n"
        f"📈 Vazn olish uchun: <b>{n.gain}</b> kkal/kun\n\n"
        "Endi ovqatingizni rasmga olib yuboring — kaloriyasini hisoblab beraman 📸"
    )


def progress_bar(eaten: int, norm: int, width: int = 10) -> str:
    if norm <= 0:
        return ""
    filled = min(width, round(width * eaten / norm))
    return "▓" * filled + "░" * (width - filled)


def remaining_line(eaten: int, norm: int) -> str:
    left = norm - eaten
    bar = progress_bar(eaten, norm)
    if left >= 0:
        return f"{bar} {eaten} / {norm} kkal\nQoldi: <b>{left}</b> kkal"
    return f"{bar} {eaten} / {norm} kkal\n⚠️ Me'yordan <b>{-left}</b> kkal oshdi"


def analysis_text(a: FoodAnalysis, totals: DayTotals | None, norm: int | None) -> str:
    lines = [f"🍽 <b>{escape(a.title)}</b>\n"]
    for item in a.items:
        lines.append(f"• {escape(item.name)} (~{item.portion_g} g) — <b>{item.kcal}</b> kkal")
    lines.append(
        f"\n🔥 Jami: <b>{a.total_kcal} kkal</b>\n"
        f"🥩 Oqsil: {fmt_num(a.total_protein_g)} g · 🧈 Yog': {fmt_num(a.total_fat_g)} g · "
        f"🍞 Uglevod: {fmt_num(a.total_carbs_g)} g\n"
        f"🎯 Aniqlik: {escape(a.confidence)}"
    )
    if a.note:
        lines.append(f"\n💡 {escape(a.note)}")
    if totals is not None and norm:
        lines.append(f"\n📊 <b>Bugun:</b>\n{remaining_line(totals.kcal, norm)}")
    elif norm is None:
        lines.append("\nKunlik me'yoringizni bilish uchun /start bosib ma'lumotlaringizni kiriting.")
    return "\n".join(lines)


def today_text(totals: DayTotals, meals: list, norm: int | None) -> str:
    if totals.meals == 0:
        text = "📊 <b>Bugun</b>\n\nHali hech narsa qayd etilmagan. Ovqat rasmini yuboring 📸"
        if norm:
            text += f"\n\nKunlik me'yor: <b>{norm}</b> kkal"
        return text
    lines = ["📊 <b>Bugun</b>\n"]
    for i, m in enumerate(meals, 1):
        lines.append(f"{i}. {escape(m['title'])} — {m['kcal']} kkal")
    lines.append(
        f"\n🥩 Oqsil: {fmt_num(totals.protein_g)} g · 🧈 Yog': {fmt_num(totals.fat_g)} g · "
        f"🍞 Uglevod: {fmt_num(totals.carbs_g)} g"
    )
    if norm:
        lines.append("\n" + remaining_line(totals.kcal, norm))
    else:
        lines.append(f"\n🔥 Jami: <b>{totals.kcal}</b> kkal")
    return "\n".join(lines)
