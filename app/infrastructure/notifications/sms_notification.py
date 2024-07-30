from app.domain.notifications.notification import Notification
from app.domain.value_objects.recipient import Recipient
from typing import List


class SmsNotification(Notification):
    def send(self, recipient: Recipient | List[Recipient], message: str) -> None:
        print(f"Sending SMS to {recipient.phone} with message: {message}")
