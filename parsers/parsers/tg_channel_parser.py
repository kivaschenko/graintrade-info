from datetime import datetime
from typing import Any, Dict, List

from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat, User

from config import TELEGRAM_API_HASH, TELEGRAM_API_ID, BASE_DIR, TELEGRAM_BOT_TOKEN
from base_parser import BaseParser

RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


class TGChannelParser(BaseParser):
    def __init__(self, session_name: str = "anonymous"):
        super().__init__()
        self.client = TelegramClient(
            session_name, int(TELEGRAM_API_ID), TELEGRAM_API_HASH
        )

    async def start(self):
        await self.client.start(bot_token=TELEGRAM_BOT_TOKEN)  # type: ignore
        print("Telegram client started")

    async def stop(self):
        await self.client.disconnect()  # type: ignore
        print("Telegram client stopped")

    async def fetch_messages(self, channel_username: str, limit: int = 100):
        entity = await self.client.get_entity(channel_username)
        if not isinstance(entity, (Channel, Chat)):
            raise ValueError(
                "The provided username does not correspond to a channel or chat."
            )

        messages = []
        async for message in self.client.iter_messages(entity, limit=limit):
            messages.append(message.to_dict())
        return messages
    
    def save_results(self, results: List[Dict[str, Any]], filepath: str, file_ext: str = "json") -> None:
        

    def parse(self, channel_username: str, limit: int = 100):
        import asyncio

        async def main():
            await self.start()
            messages = await self.fetch_messages(channel_username, limit)
            # Save messages to a file
            datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"{RESULTS_DIR}/{channel_username}_{datetime_str}_messages.json"
            self.save_results(messages, file_path)
            await self.stop()
            return messages

        return asyncio.run(main())


if __name__ == "__main__":
    parser = TGChannelParser()
    channel_username = "Zernovaya_Birzha"  # Example channel username
    messages = parser.parse(channel_username, limit=50)
    print(f"Fetched {len(messages)} messages from {channel_username}")
