import pytest

from bot.db import Database, Profile


@pytest.fixture
async def db(tmp_path):
    d = Database(str(tmp_path / "t.db"))
    await d.connect()
    yield d
    await d.close()


async def test_profile_upsert(db):
    assert await db.get_profile(1) is None
    await db.save_profile(Profile(1, "male", 25, 175, 70, "moderate", 2594))
    await db.save_profile(Profile(1, "male", 26, 175, 72, "light", 2400))
    p = await db.get_profile(1)
    assert (p.age, p.weight_kg, p.daily_kcal) == (26, 72, 2400)


async def test_meals_totals_and_delete(db):
    m1 = await db.add_meal(1, "2026-11-18", "Osh", 600, 20, 25, 70)
    await db.add_meal(1, "2026-11-18", "Choy", 40, 0, 0, 10)
    await db.add_meal(1, "2026-11-17", "Somsa", 300, 10, 15, 30)
    await db.add_meal(2, "2026-11-18", "Boshqa", 999, 0, 0, 0)
    t = await db.day_totals(1, "2026-11-18")
    assert (t.kcal, t.meals) == (640, 2)
    assert not await db.delete_meal(2, m1)  # boshqa foydalanuvchi o'chira olmaydi
    assert await db.delete_meal(1, m1)
    t = await db.day_totals(1, "2026-11-18")
    assert t.kcal == 40
    assert [m["title"] for m in await db.day_meals(1, "2026-11-18")] == ["Choy"]
