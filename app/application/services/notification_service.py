from app.domain.services.notification import Notification
from app.domain.value_objects.recipient import Recipient
from typing import List


class NotificationService:
    def __init__(self, notifications: list[Notification]):
        self.notifications = notifications

    def send_notification(
        self, recipient: Recipient | List[Recipient], message: str
    ) -> None:
        self.notification.send(recipient, message)
