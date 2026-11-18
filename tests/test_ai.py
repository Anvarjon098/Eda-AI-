import json
from types import SimpleNamespace

import pytest

from bot.ai import AnalysisError, FoodAnalyzer, parse_analysis

SAMPLE = {
    "is_food": True,
    "title": "Osh",
    "items": [
        {"name": "Osh", "portion_g": 350, "kcal": 600, "protein_g": 20, "fat_g": 25, "carbs_g": 70},
        {"name": "Achchiq-chuchuk", "portion_g": 100, "kcal": 25, "protein_g": 1, "fat_g": 0.5, "carbs_g": 4},
    ],
    "total_kcal": 999,  # noto'g'ri yig'indi — tuzatilishi kerak
    "total_protein_g": 0, "total_fat_g": 0, "total_carbs_g": 0,
    "confidence": "o'rtacha",
    "note": "Yog'li taom.",
}


def test_parse_recomputes_totals():
    a = parse_analysis(json.dumps(SAMPLE))
    assert a.total_kcal == 625
    assert a.total_protein_g == 21
    assert a.total_fat_g == 25.5


def test_parse_invalid():
    with pytest.raises(AnalysisError):
        parse_analysis("not json")
    with pytest.raises(AnalysisError):
        parse_analysis(json.dumps({"is_food": True}))


class FakeMessages:
    def __init__(self, response):
        self.response = response
        self.kwargs = None

    async def create(self, **kwargs):
        self.kwargs = kwargs
        return self.response


def fake_client(response):
    messages = FakeMessages(response)
    return SimpleNamespace(beta=SimpleNamespace(messages=messages)), messages


async def test_analyze_builds_request():
    resp = SimpleNamespace(stop_reason="end_turn", stop_details=None,
                           content=[SimpleNamespace(type="text", text=json.dumps(SAMPLE))])
    client, messages = fake_client(resp)
    analyzer = FoodAnalyzer("key", "claude-opus-5-5", client=client)
    a = await analyzer.analyze(b"\xff\xd8img", "image/jpeg", "2 porsiya")
    assert a.title == "Osh"
    kw = messages.kwargs
    assert kw["model"] == "claude-opus-5-5"
    assert kw["fallbacks"] == "default"
    assert kw["output_config"]["format"]["type"] == "json_schema"
    content = kw["messages"][0]["content"]
    assert content[0]["type"] == "image"
    assert "2 porsiya" in content[1]["text"]


async def test_analyze_refusal():
    resp = SimpleNamespace(stop_reason="refusal", stop_details=None, content=[])
    client, _ = fake_client(resp)
    with pytest.raises(AnalysisError):
        await FoodAnalyzer("key", client=client).analyze(b"x")
