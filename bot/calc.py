"""Kunlik kaloriya sarfini hisoblash (Mifflin–St Jeor formulasi)."""
from dataclasses import dataclass

# Jismoniy faollik koeffitsientlari
ACTIVITY_LEVELS: dict[str, tuple[float, str]] = {
    "sedentary": (1.2, "Kam harakat (ofis ishi, sport yo'q)"),
    "light": (1.375, "Yengil (haftada 1–3 marta sport)"),
    "moderate": (1.55, "O'rtacha (haftada 3–5 marta sport)"),
    "active": (1.725, "Faol (haftada 6–7 marta sport)"),
    "very_active": (1.9, "Juda faol (og'ir jismoniy ish)"),
}

AGE_RANGE = (10, 100)
HEIGHT_RANGE = (100, 250)  # sm
WEIGHT_RANGE = (25, 300)  # kg


@dataclass(frozen=True)
class DailyNeeds:
    bmr: int  # tinch holatdagi sarf
    tdee: int  # kunlik umumiy sarf (vaznni saqlash uchun)
    lose: int  # vazn tashlash uchun (~0.5 kg/hafta)
    gain: int  # vazn olish uchun
    bmi: float


def bmr(sex: str, age: int, height_cm: float, weight_kg: float) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if sex == "male" else base - 161


def daily_needs(sex: str, age: int, height_cm: float, weight_kg: float, activity: str) -> DailyNeeds:
    factor = ACTIVITY_LEVELS[activity][0]
    b = bmr(sex, age, height_cm, weight_kg)
    tdee = b * factor
    # Juda past kaloriyaga tushib ketmaslik uchun pastki chegara
    floor = 1500 if sex == "male" else 1200
    lose = max(tdee - 500, floor)
    bmi = weight_kg / (height_cm / 100) ** 2
    return DailyNeeds(
        bmr=round(b),
        tdee=round(tdee),
        lose=round(lose),
        gain=round(tdee + 400),
        bmi=round(bmi, 1),
    )


def bmi_label(bmi: float) -> str:
    if bmi < 18.5:
        return "vazn yetishmaydi"
    if bmi < 25:
        return "normal vazn"
    if bmi < 30:
        return "ortiqcha vazn"
    return "semizlik"


def parse_number(text: str, lo: float, hi: float) -> float | None:
    """'175', '72.5', '72,5 kg' kabi matndan sonni ajratadi; chegaradan tashqarisi None."""
    cleaned = text.strip().lower().replace(",", ".")
    for suffix in ("kg", "sm", "cm", "yosh", "yil"):
        cleaned = cleaned.removesuffix(suffix).strip()
    try:
        value = float(cleaned)
    except ValueError:
        return None
    return value if lo <= value <= hi else None
