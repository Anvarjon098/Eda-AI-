import pytest

from bot.calc import bmi_label, bmr, daily_needs, parse_number


def test_bmr_mifflin():
    # 10*70 + 6.25*175 - 5*25 + 5 = 1673.75
    assert bmr("male", 25, 175, 70) == pytest.approx(1673.75)
    # 10*60 + 6.25*165 - 5*30 - 161 = 1320.25
    assert bmr("female", 30, 165, 60) == pytest.approx(1320.25)


def test_daily_needs():
    n = daily_needs("male", 25, 175, 70, "moderate")
    assert n.bmr == 1674
    assert n.tdee == round(1673.75 * 1.55)
    assert n.lose == n.tdee - 500
    assert n.gain == n.tdee + 400
    assert n.bmi == 22.9


def test_lose_has_floor():
    n = daily_needs("female", 80, 150, 40, "sedentary")
    assert n.lose == 1200


@pytest.mark.parametrize("text,expected", [
    ("175", 175), ("72,5", 72.5), ("72.5 kg", 72.5), (" 180sm ", 180), ("25 yosh", 25),
])
def test_parse_number_ok(text, expected):
    assert parse_number(text, 10, 300) == expected


@pytest.mark.parametrize("text", ["abc", "", "5", "1000", "-70"])
def test_parse_number_bad(text):
    assert parse_number(text, 10, 300) is None


def test_bmi_label():
    assert bmi_label(17) == "vazn yetishmaydi"
    assert bmi_label(22) == "normal vazn"
    assert bmi_label(27) == "ortiqcha vazn"
    assert bmi_label(32) == "semizlik"


def test_token_extracted_from_botfather_message(monkeypatch, tmp_path):
    from bot import config
    tok = "907229000:" + "A" * 35
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    monkeypatch.setenv("BOT_TOKEN", f"Done! Use this token to access the HTTP API: {tok} Keep your token secure")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    assert config.load_config().bot_token == tok
