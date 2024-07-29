from app.domain.notifications.notification import Notification
from app.domain.value_objects.recipient import Recipient


class EmailNotification(Notification):
    def send(self, recipient: Recipient, message: str) -> None:
        print(f"Sending email to {recipient.email} with message: {message}")
