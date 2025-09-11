from pathlib import Path
import os
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", "29202578")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "e8c4f3b1f0f5e6d5f4c3b2a1d0e9f8g7")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

print(
    f"Config loaded: TELEGRAM_API_ID={TELEGRAM_API_ID}, TELEGRAM_API_HASH={'set' if TELEGRAM_API_HASH else 'not set'}"
)
