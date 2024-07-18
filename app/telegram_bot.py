from telegram.ext import Updater, CommandHandler
import logging
from dotenv import load_dotenv
import os

load_dotenv()

# Telegram Bot Token
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text("Hi! Use /get to perform a read operation.")


def get_data(update, context):
    """Perform a read operation."""
    # Here, you would integrate with your backend to fetch data
    data = "This is the data from your backend."
    update.message.reply_text(data)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


# def main():
#     """Start the bot."""
#     updater = Updater(TOKEN, use_context=True)

#     # Get the dispatcher to register handlers
#     dp = updater.dispatcher

#     # On different commands - answer in Telegram
#     dp.add_handler(CommandHandler("start", start))
#     dp.add_handler(CommandHandler("get", get_data))

#     # Log all errors
#     dp.add_error_handler(error)

#     # Start the Bot
#     updater.start_polling()
#     updater.idle()

# if __name__ == '__main__':
#     main()
import asyncio
import telegram


async def main():
    bot = telegram.Bot(TOKEN)
    async with bot:
        print(await bot.get_me())
        updates = (await bot.get_updates())[0]
        print(updates)


if __name__ == "__main__":
    asyncio.run(main())
