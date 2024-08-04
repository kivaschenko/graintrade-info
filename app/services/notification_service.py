from app.domain.notification import Notification
from app.domain.recipient import Recipient
from typing import List


class NotificationService:
    def __init__(self, notifications: list[Notification]):
        self.notifications = notifications

    def send_notification(
        self, recipient: Recipient | List[Recipient], message: str
    ) -> None:
        self.notification.send(recipient, message)


class EmailNotification(Notification):
    def send(self, recipient: Recipient | List[Recipient], message: str) -> None:
        print(f"Sending email to {recipient.email} with message: {message}")


class SMSNotification(Notification):
    def send(self, recipient: Recipient | List[Recipient], message: str) -> None:
        print(f"Sending SMS to {recipient.phone} with message: {message}")


class PushNotification(Notification):
    def send(self, recipient: Recipient | List[Recipient], message: str) -> None:
        print(
            f"Sending push notification to {recipient.device_id} with message: {message}"
        )


class TelegramNotification(Notification):
    def send(self, recipient: Recipient | List[Recipient], message: str) -> None:
        print(f"Sending Telegram to {recipient.telegram_id} with message: {message}")


class ViberNotification(Notification):
    def send(self, recipient: Recipient | List[Recipient], message: str) -> None:
        print(f"Sending Viber to {recipient.viber_id} with message: {message}")
