import logging

from telegram import Bot
from telegram.constants import ParseMode

from ..config import TELEGRAM_TOKEN
from ..metrics import (
    EXTERNAL_SERVICE_ERRORS,
    FAILED_NOTIFICATIONS_COUNT,
    NOTIFICATIONS_SENT_COUNT,
)


if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set in .env")

bot = Bot(token=TELEGRAM_TOKEN)


async def send_telegram_message(
    chat_id: str, text: str, parse_mode: str = ParseMode.HTML
):
    """Send a telegram message and return the Message object.

    Returns None on failure.
    """
    if not bot:
        logging.warning("Telegram disabled: TELEGRAM_TOKEN not set")
        FAILED_NOTIFICATIONS_COUNT.labels(channel="telegram", reason="disabled").inc()
        return None
    try:
        message = await bot.send_message(
            chat_id=chat_id, text=text, parse_mode=parse_mode
        )
        logging.info(
            f"[TELEGRAM] Sent message_id={message.message_id} to chat_id={message.chat.id}"
        )
        NOTIFICATIONS_SENT_COUNT.labels(channel="telegram").inc()
        return message
    except Exception as e:
        error_type = e.__class__.__name__
        FAILED_NOTIFICATIONS_COUNT.labels(channel="telegram", reason=error_type).inc()
        EXTERNAL_SERVICE_ERRORS.labels(
            service_name="telegram", error_type=error_type
        ).inc()
        logging.error(f"Telegram send error (chat {chat_id}): {e}")
        return None


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


async def delete_telegram_message(chat_id: int, message_id: int) -> bool:
    """Delete a telegram message. Returns True on success, False on failure."""
    logging.info(f"Deleting telegram message_id={message_id} in chat_id={chat_id}")
    if not bot:
        logging.warning("Telegram disabled: TELEGRAM_TOKEN not set")
        return False
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logging.info(f"[TELEGRAM] Deleted message_id={message_id} in chat_id={chat_id}")
        return True
    except Exception as e:
        error_type = e.__class__.__name__
        EXTERNAL_SERVICE_ERRORS.labels(
            service_name="telegram", error_type=error_type
        ).inc()
        FAILED_NOTIFICATIONS_COUNT.labels(
            channel="telegram", reason="delete_failed"
        ).inc()
        logging.error(
            f"Telegram delete message error for message_id={message_id} chat_id={chat_id}: {e}"
        )
        return False
