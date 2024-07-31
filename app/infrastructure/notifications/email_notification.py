from app.domain.services.notification import Notification
from app.domain.value_objects.recipient import Recipient
from typing import List


class EmailNotification(Notification):
    def send(self, recipient: Recipient | List[Recipient], message: str) -> None:
        print(f"Sending email to {recipient.email} with message: {message}")
