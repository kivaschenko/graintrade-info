from app.domain.notifications.notification import Notification
from app.domain.value_objects.recipient import Recipient


class SmsNotification(Notification):
    def send(self, recipient: Recipient, message: str) -> None:
        print(f"Sending SMS to {recipient.phone} with message: {message}")
