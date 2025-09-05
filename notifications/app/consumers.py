import json
import logging
import aio_pika
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from .config import (
    BASE_URL,
    TELEGRAM_CHANNEL_ID,
    ENABLE_EMAIL,
    ENABLE_TELEGRAM,
    ENABLE_VIBER,
)
from .channels.email import send_email
from .channels.telegram_ptb import send_telegram_message
from .channels.viber import send_viber_message

BASE_DIR = Path(__file__).resolve().parent.parent
env = Environment(loader=FileSystemLoader(BASE_DIR / "templates"))


# === Example handler for new item ===
async def handle_item_notification(msg: aio_pika.abc.AbstractIncomingMessage):
    async with msg.process():
        data = json.loads(msg.body.decode())

        # Telegram broadcast
        if ENABLE_TELEGRAM and TELEGRAM_CHANNEL_ID:
            tg_text = (
                f"🆕 <b>{data['title']}</b>\n"
                f"{data.get('description', 'Опис відсутній')}\n\n"
                f"💰 {data.get('price')} {data.get('currency')} | {data.get('amount')} {data.get('measure')}\n"
                f"📍 {data.get('country')}{', ' + data.get('region') if data.get('region') else ''}\n"
                f"➡ <a href='{BASE_URL}/items/{data['id']}'>Детальніше</a>"
            )
            await send_telegram_message(TELEGRAM_CHANNEL_ID, tg_text)

        # Viber broadcast to users (if you have IDs)
        if ENABLE_VIBER:
            viber_text = (
                f"🆕 Новий товар!\n"
                f"{data['title']}\n"
                f"Ціна: {data.get('price')} {data.get('currency')}\n"
                f"Деталі: {BASE_URL}/items/{data['id']}"
            )
            # Example: if you collect viber_ids in DB
            # for pref in preferences: await send_viber_message(pref.viber_id, viber_text)
