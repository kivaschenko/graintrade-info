# services.py

from pathlib import Path
from dotenv import load_dotenv
import os
import httpx
from telegram import Bot
from telegram.error import TelegramError
from abc import ABC, abstractmethod
from .schemas import Recipient  # Import the Recipient class from the .schemas module

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

EMAIL_API_KEY = os.getenv("EMAIL_API_KEY")
SMS_API_KEY = os.getenv("SMS_API_KEY")
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")


class NotificationHandler(ABC):
    @classmethod
    @abstractmethod
    def send(self, recipient: Recipient, message: str) -> None:
        pass


class EmailNotificationHandler(NotificationHandler):
    @classmethod
    async def send(cls, recipient: Recipient, message: str) -> bool:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.emailservice.com/send",
                headers={"Authorization": f"Bearer {EMAIL_API_KEY}"},
                json={"to": recipient.email, "message": message},
            )
        return response.status_code == 200


class SMSNotificationHandler(NotificationHandler):
    @classmethod
    async def send(cls, recipient: Recipient, message: str) -> bool:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.smsservice.com/send",
                headers={"Authorization": f"Bearer {SMS_API_KEY}"},
                json={"to": recipient.phone, "message": message},
            )
        return response.status_code == 200


class TelegramNotificationHandler(NotificationHandler):
    @classmethod
    async def send(cls, recipient: Recipient, message: str) -> bool:
        bot = Bot(token=TELEGRAM_API_KEY)
        try:
            await bot.send_message(chat_id=recipient.telegram_id, text=message)
            return True
        except TelegramError:
            return False


# class NotificationService:
#     def __init__(self, notifications: list[NotificationHandler]):
#         self.notifications = notifications

#     async def send_notification(self, recipient: Recipient, message: str) -> None:
#         for notification in self.notifications:
#             await notification.send(recipient, message)
