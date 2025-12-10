from pathlib import Path
import os
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Core
DATABASE_URL = os.getenv("DATABASE_URL")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://user:password@localhost:5672/")
REDIS_URL = os.getenv("REDIS_URL")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")

# Channels toggles
ENABLE_EMAIL = os.getenv("ENABLE_EMAIL", "true").lower() == "true"
ENABLE_TELEGRAM = os.getenv("ENABLE_TELEGRAM", "true").lower() == "true"
ENABLE_VIBER = os.getenv("ENABLE_VIBER", "false").lower() == "true"

# Email (SMTP or Mailtrap)
SMTP_USER = os.getenv("MAILTRAP_USER")
SMTP_PASS = os.getenv("MAILTRAP_PASS")
SMTP_HOST = os.getenv("MAILTRAP_HOST", "live.smtp.mailtrap.io")
SMTP_PORT = int(os.getenv("MAILTRAP_PORT", 587))
EMAIL_FROM = os.getenv("EMAIL_FROM")
BULK_MAILTRAP_HOST = os.getenv("BULK_MAILTRAP_HOST", "bulk.smtp.mailtrap.io")
BULK_MAILTRAP_PASS = os.getenv("BULK_MAILTRAP_PASS")

# Telegram (PTB)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

# Viber
VIBER_TOKEN = os.getenv("VIBER_TOKEN")
VIBER_API_URL = "https://chatapi.viber.com/pa/send_message"

# Preferences
PREFERENCES_MODE = os.getenv("PREFERENCES_MODE", "db")

# Metrics
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"
METRICS_HOST = os.getenv("METRICS_HOST", "0.0.0.0")
METRICS_PORT = int(os.getenv("METRICS_PORT", 9108))
