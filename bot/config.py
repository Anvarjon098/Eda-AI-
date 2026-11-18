import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    bot_token: str
    anthropic_api_key: str
    claude_model: str
    db_path: str
    timezone: ZoneInfo


def load_config() -> Config:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("BOT_TOKEN .env faylida ko'rsatilmagan")
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY .env faylida ko'rsatilmagan")
    return Config(
        bot_token=token,
        anthropic_api_key=api_key,
        claude_model=os.getenv("CLAUDE_MODEL", "claude-opus-5-5").strip(),
        db_path=os.getenv("DB_PATH", "eda.db").strip(),
        timezone=ZoneInfo(os.getenv("TIMEZONE", "Asia/Tashkent").strip()),
    )
