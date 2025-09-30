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
        message = await bot.send_message(
            chat_id=chat_id, text=text, parse_mode=parse_mode
        )
        logging.info(f"[TELEGRAM] -> {chat_id} Message ID: {message.message_id}")
        return message
    except Exception as e:
        logging.error(f"Telegram error: {e}")
        return 0


# Message(
# channel_chat_created=False,
# chat=Chat(id=-1003098631999, title='Graintrade.info - зернова біржа', type=<ChatType.CHANNEL>, username='graintradeinfo'),
# date=datetime.datetime(2025, 9, 30, 7, 34, 12, tzinfo=datetime.timezone.utc),
# delete_chat_photo=False,
# entities=(
# MessageEntity(length=30, offset=3, type=<MessageEntityType.BOLD>),
# MessageEntity(length=13, offset=38, type=<MessageEntityType.BOLD>),
# MessageEntity(length=19, offset=65, type=<MessageEntityType.BOLD>),
# MessageEntity(length=14, offset=102, type=<MessageEntityType.BOLD>),
# MessageEntity(length=18, offset=142, type=<MessageEntityType.BOLD>),
# MessageEntity(length=19, offset=168, type=<MessageEntityType.BOLD>)
# ),
# group_chat_created=False,
# message_id=83,
# sender_chat=Chat(id=-1003098631999, title='Graintrade.info - зернова біржа', type=<ChatType.CHANNEL>, username='graintradeinfo'), supergroup_chat_created=False, text='🔴 Купую Коріандр (Buy Coriander)\n\n💰 Ціна (Price): 550.0 USD\n📦 Кількість (Amount): 20 metric ton\n📍 Місце (Point): Ukraine, Odesa Oblast\n🚚 Умови (Incoterms): CPT\n   Опис (Description): \n\n➡️ Детальніше (Details)')


async def delete_telegram_message(chat_id: int, message_id: int):
    if not bot:
        logging.warning("Telegram disabled: TELEGRAM_TOKEN not set")
        return
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logging.info(f"[TELEGRAM] Deleted message {message_id} in chat {chat_id}")
    except Exception as e:
        logging.error(f"Telegram delete message error: {e}")
        return False
