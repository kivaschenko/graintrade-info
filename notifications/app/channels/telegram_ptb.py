import logging

from telegram import Bot
from telegram.constants import ParseMode

from ..config import TELEGRAM_TOKEN


if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set in .env")

bot = Bot(token=TELEGRAM_TOKEN)


async def send_telegram_message(
    chat_id: str, text: str, parse_mode: str = ParseMode.HTML
):
    if not bot:
        logging.warning("Telegram disabled: TELEGRAM_TOKEN not set")
        return
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
        logging.info(f"[TELEGRAM] -> {chat_id}")
    except Exception as e:
        logging.error(f"Telegram error: {e}")
