from app.domain.notifications.notification import Notification
from app.domain.value_objects.recipient import Recipient
from typing import List


class TelegramNotification(Notification):
    def send(self, recipient: Recipient | List[Recipient], message: str) -> None:
        print(f"Sending Telegram to {recipient.telegram_id} with message: {message}")


# Compare this snippet from app/domain/notifications/notification.py:
# from abc import ABC, abstractmethod
# from app.domain.notifications.recipient import Recipient
