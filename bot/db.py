from dataclasses import dataclass

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    sex         TEXT NOT NULL,
    age         INTEGER NOT NULL,
    height_cm   REAL NOT NULL,
    weight_kg   REAL NOT NULL,
    activity    TEXT NOT NULL,
    daily_kcal  INTEGER NOT NULL,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS meals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    day         TEXT NOT NULL,          -- YYYY-MM-DD, foydalanuvchi vaqt mintaqasida
    title       TEXT NOT NULL,
    kcal        INTEGER NOT NULL,
    protein_g   REAL NOT NULL,
    fat_g       REAL NOT NULL,
    carbs_g     REAL NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_meals_user_day ON meals(user_id, day);
"""


@dataclass
class Profile:
    user_id: int
    sex: str
    age: int
    height_cm: float
    weight_kg: float
    activity: str
    daily_kcal: int


@dataclass
class DayTotals:
    kcal: int
    protein_g: float
    fat_g: float
    carbs_g: float
    meals: int


class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.conn.executescript(SCHEMA)
        await self.conn.commit()

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()

    async def save_profile(self, p: Profile) -> None:
        await self.conn.execute(
            """INSERT INTO users (user_id, sex, age, height_cm, weight_kg, activity, daily_kcal)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                 sex=excluded.sex, age=excluded.age, height_cm=excluded.height_cm,
                 weight_kg=excluded.weight_kg, activity=excluded.activity,
                 daily_kcal=excluded.daily_kcal, updated_at=datetime('now')""",
            (p.user_id, p.sex, p.age, p.height_cm, p.weight_kg, p.activity, p.daily_kcal),
        )
        await self.conn.commit()

    async def get_profile(self, user_id: int) -> Profile | None:
        async with self.conn.execute(
            "SELECT user_id, sex, age, height_cm, weight_kg, activity, daily_kcal FROM users WHERE user_id=?",
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
        return Profile(**dict(row)) if row else None

    async def add_meal(self, user_id: int, day: str, title: str, kcal: int,
                       protein_g: float, fat_g: float, carbs_g: float) -> int:
        cur = await self.conn.execute(
            "INSERT INTO meals (user_id, day, title, kcal, protein_g, fat_g, carbs_g) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, day, title, kcal, protein_g, fat_g, carbs_g),
        )
        await self.conn.commit()
        return cur.lastrowid

    async def delete_meal(self, user_id: int, meal_id: int) -> bool:
        cur = await self.conn.execute("DELETE FROM meals WHERE id=? AND user_id=?", (meal_id, user_id))
        await self.conn.commit()
        return cur.rowcount > 0

    async def day_totals(self, user_id: int, day: str) -> DayTotals:
        async with self.conn.execute(
            """SELECT COALESCE(SUM(kcal),0) AS kcal, COALESCE(SUM(protein_g),0) AS protein_g,
                      COALESCE(SUM(fat_g),0) AS fat_g, COALESCE(SUM(carbs_g),0) AS carbs_g,
                      COUNT(*) AS meals
               FROM meals WHERE user_id=? AND day=?""",
            (user_id, day),
        ) as cur:
            row = await cur.fetchone()
        return DayTotals(**dict(row))

    async def day_meals(self, user_id: int, day: str) -> list[aiosqlite.Row]:
        async with self.conn.execute(
            "SELECT id, title, kcal FROM meals WHERE user_id=? AND day=? ORDER BY id", (user_id, day)
        ) as cur:
            return list(await cur.fetchall())
