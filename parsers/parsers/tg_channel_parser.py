from datetime import datetime
from typing import Any, Dict, List

from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat, User

from config import TELEGRAM_API_HASH, TELEGRAM_API_ID, BASE_DIR, TELEGRAM_BOT_TOKEN
from base_parser import BaseParser

RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


class TGChannelParser(BaseParser):
    def __init__(self, session_name: str = "session"):
        super().__init__()
        self.client = TelegramClient(
            session_name, int(TELEGRAM_API_ID), TELEGRAM_API_HASH
        )

    async def start(self):
        await self.client.start(
            phone="+380662760451",
            # bot_token=TELEGRAM_BOT_TOKEN,
        )  # type: ignore
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

    def save_results(
        self, results: List[Dict[str, Any]], filepath: str, file_ext: str = "json"
    ) -> None:
        messages = []
        for result in results:
            try:
                from_id = result.get("from_id")
                if from_id is None:
                    sender_id = None
                else:
                    sender_id = (
                        result.get("from_id").user_id
                        if hasattr(result.get("from_id"), "user_id")
                        else None
                    )
            except Exception as e:
                print(f"Error occurred while processing from_id: {e}")

            finally:
                pass
            message_info = {
                "id": result.get("id"),
                "date": result.get("date").strftime("%Y-%m-%d %H:%M:%S")  # type: ignore
                if result.get("date")
                else None,
                "message": result.get("message"),
                "sender_id": sender_id,
            }
            messages.append(message_info)
        import json

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json.dumps(messages, ensure_ascii=False, indent=4))
            print(f"Results saved to {filepath}")

    def parse(self, channel_username: str, limit: int = 100):
        import asyncio

        async def main():
            await self.start()
            messages = await self.fetch_messages(channel_username, limit)
            datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Save messages to a file
            file_path = f"{RESULTS_DIR}/{channel_username}_messages_{datetime_str}.json"
            self.save_results(messages, file_path)
            await self.stop()
            return messages

        return asyncio.run(main())


if __name__ == "__main__":
    parser = TGChannelParser()
    channel_username = "Zernovaya_Birzha"  # Example channel username
    messages = parser.parse(channel_username, limit=100)
    print(f"Fetched {len(messages)} messages from {channel_username}")
