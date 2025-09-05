from pathlib import Path
import os
import logging
import asyncio
from dotenv import load_dotenv
import telegram

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def main():
    bot = telegram.Bot(token=TOKEN)
    async with bot:
        print(await bot.get_me())


if __name__ == "__main__":
    asyncio.run(main())
