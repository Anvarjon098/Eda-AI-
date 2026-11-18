"""Ovqat rasmini Claude orqali tahlil qilish."""
import base64
import json
import logging

import anthropic
from pydantic import BaseModel, ValidationError

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Siz tajribali dietolog va ovqatlanish bo'yicha mutaxassissiz. Foydalanuvchi ovqat rasmini yuboradi.
Vazifangiz: rasmdagi har bir taom yoki mahsulotni aniqlash, porsiya hajmini (gramm) baholash va
kaloriya hamda oqsil/yog'/uglevod miqdorini hisoblash.

Qoidalar:
- O'zbek, Markaziy Osiyo va jahon taomlarini yaxshi bilasiz (osh, lag'mon, somsa, manti, shashlik,
  non, chuchvara va h.k.). Taom nomlarini o'zbek tilida (lotin yozuvida) yozing.
- Porsiyani idish, qoshiq, qo'l kabi atrofdagi narsalarga qarab baholang. Aniq bilmasangiz,
  o'rtacha porsiyani oling va buni ishonch darajasida aks ettiring.
- Yog' bilan pishirilgan taomlarda (osh, qovurdoq, somsa) yog'ni hisobga oling.
- Ichimliklar ham hisoblanadi (shakarli choy, sharbat, gazli suv).
- Agar foydalanuvchi izoh yozgan bo'lsa (masalan, porsiya hajmi yoki tarkibi), uni ustun deb biling.
- Rasmda ovqat bo'lmasa, is_food=false qiling, items bo'sh ro'yxat va jami qiymatlar 0 bo'lsin,
  note maydonida rasmda nima borligini qisqa yozing.
- note maydoniga 1–2 jumlali foydali, qisqa izoh yozing (o'zbek tilida).
- total_* qiymatlari items yig'indisiga teng bo'lsin.
"""


class FoodItem(BaseModel):
    name: str
    portion_g: int
    kcal: int
    protein_g: float
    fat_g: float
    carbs_g: float


class FoodAnalysis(BaseModel):
    is_food: bool
    title: str
    items: list[FoodItem]
    total_kcal: int
    total_protein_g: float
    total_fat_g: float
    total_carbs_g: float
    confidence: str  # "past" | "o'rtacha" | "yuqori"
    note: str


OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "is_food": {"type": "boolean", "description": "Rasmda ovqat yoki ichimlik bormi"},
        "title": {"type": "string", "description": "Taomning qisqa umumiy nomi, masalan 'Osh va salat'"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "portion_g": {"type": "integer", "description": "Taxminiy og'irlik, gramm"},
                    "kcal": {"type": "integer"},
                    "protein_g": {"type": "number"},
                    "fat_g": {"type": "number"},
                    "carbs_g": {"type": "number"},
                },
                "required": ["name", "portion_g", "kcal", "protein_g", "fat_g", "carbs_g"],
                "additionalProperties": False,
            },
        },
        "total_kcal": {"type": "integer"},
        "total_protein_g": {"type": "number"},
        "total_fat_g": {"type": "number"},
        "total_carbs_g": {"type": "number"},
        "confidence": {"type": "string", "enum": ["past", "o'rtacha", "yuqori"]},
        "note": {"type": "string"},
    },
    "required": [
        "is_food", "title", "items", "total_kcal", "total_protein_g",
        "total_fat_g", "total_carbs_g", "confidence", "note",
    ],
    "additionalProperties": False,
}


class AnalysisError(Exception):
    """Foydalanuvchiga ko'rsatiladigan xabar bilan xato."""


class FoodAnalyzer:
    def __init__(self, api_key: str, model: str = "claude-opus-5-5", client: anthropic.AsyncAnthropic | None = None):
        self.model = model
        self.client = client or anthropic.AsyncAnthropic(api_key=api_key, max_retries=3, timeout=120.0)

    async def analyze(self, image: bytes, media_type: str = "image/jpeg", caption: str | None = None) -> FoodAnalysis:
        content: list[dict] = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64.standard_b64encode(image).decode("ascii"),
                },
            },
        ]
        text = "Ushbu rasmdagi ovqatning kaloriyasini hisoblang."
        if caption:
            text += f"\nFoydalanuvchi izohi: {caption.strip()[:500]}"
        content.append({"type": "text", "text": text})

        request = dict(
            model=self.model,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
        )
        try:
            try:
                response = await self.client.beta.messages.create(
                    **request,
                    betas=["server-side-fallback-2026-07-01"],
                    fallbacks="default",
                )
            except anthropic.BadRequestError as e:
                # Hisobda fallback beta yoqilmagan bo'lsa yoki model uni qo'llamasa — fallback'siz qayta so'raymiz
                if "fallback" not in str(e).lower() and "beta" not in str(e).lower():
                    raise
                log.warning("Fallback'siz qayta so'ralmoqda: %s", e)
                response = await self.client.messages.create(**request)
        except anthropic.RateLimitError as e:
            log.warning("Claude rate limit: %s", e)
            raise AnalysisError("Hozir so'rovlar juda ko'p. Bir daqiqadan keyin qayta urinib ko'ring.") from e
        except anthropic.BadRequestError as e:
            log.error("Claude bad request: %s", e)
            raise AnalysisError(bad_request_message(str(e))) from e
        except anthropic.AuthenticationError as e:
            log.error("Claude API kaliti noto'g'ri: %s", e)
            raise AnalysisError("ANTHROPIC_API_KEY noto'g'ri. Administrator .env faylidagi kalitni tekshirsin.") from e
        except anthropic.PermissionDeniedError as e:
            log.error("Claude API ruxsat yo'q: %s", e)
            raise AnalysisError("API kalitiga bu modeldan foydalanishga ruxsat yo'q. Administratorga xabar bering.") from e
        except anthropic.NotFoundError as e:
            log.error("Claude modeli topilmadi (%s): %s", self.model, e)
            raise AnalysisError(f"«{self.model}» modeli topilmadi. .env dagi CLAUDE_MODEL ni tekshiring.") from e
        except anthropic.APIStatusError as e:
            log.error("Claude API xatosi %s: %s", e.status_code, e)
            raise AnalysisError("AI xizmatida vaqtinchalik nosozlik. Birozdan keyin urinib ko'ring.") from e
        except anthropic.APIConnectionError as e:
            log.error("Claude bilan aloqa yo'q: %s", e)
            raise AnalysisError("AI xizmatiga ulanib bo'lmadi. Server internetini tekshiring.") from e

        if response.stop_reason == "refusal":
            log.warning("Claude refusal: %s", response.stop_details)
            raise AnalysisError("Bu rasmni tahlil qilib bo'lmadi. Ovqat rasmini yuboring.")
        if response.stop_reason == "max_tokens":
            raise AnalysisError("Javob to'liq kelmadi. Qayta urinib ko'ring.")

        raw = next((b.text for b in response.content if b.type == "text"), "")
        return parse_analysis(raw)


def bad_request_message(error: str) -> str:
    e = error.lower()
    if "credit balance" in e or "billing" in e:
        return ("Claude API hisobida mablag' qolmagan. Administrator platform.claude.com → "
                "Billing bo'limida balansni to'ldirishi kerak.")
    if "image" in e:
        return "Rasmni o'qib bo'lmadi. Boshqa rasm yuborib ko'ring (JPG yoki PNG)."
    return "AI so'rovni qabul qilmadi. Administrator bot loglarini tekshirsin."


def parse_analysis(raw: str) -> FoodAnalysis:
    try:
        result = FoodAnalysis.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValidationError) as e:
        log.error("Claude javobini o'qib bo'lmadi: %r", raw[:500])
        raise AnalysisError("AI javobini tushunib bo'lmadi. Qayta urinib ko'ring.") from e
    # Jami qiymat elementlar yig'indisidan farq qilsa, yig'indiga ishonamiz
    if result.items:
        result.total_kcal = sum(i.kcal for i in result.items)
        result.total_protein_g = round(sum(i.protein_g for i in result.items), 1)
        result.total_fat_g = round(sum(i.fat_g for i in result.items), 1)
        result.total_carbs_g = round(sum(i.carbs_g for i in result.items), 1)
    return result
