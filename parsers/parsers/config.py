from pathlib import Path
import os
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", "29202578")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "e8c4f3b1f0f5e6d5f4c3b2a1d0e9f8g7")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_PASSWORD = os.getenv("TELEGRAM_PASSWORD", "")

print(
    f"Config loaded: TELEGRAM_API_ID={TELEGRAM_API_ID}, TELEGRAM_API_HASH={'set' if TELEGRAM_API_HASH else 'not set'}"
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/dbname"
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
print(
    f"Config loaded: OPENAI_API_KEY={'set' if OPENAI_API_KEY else 'not set'}, DATABASE_URL={DATABASE_URL}, REDIS_URL={REDIS_URL}"
)
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOTEN is not set in environment variables")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in environment variables")
