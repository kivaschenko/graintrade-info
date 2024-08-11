from abc import ABC, abstractmethod
from .recipient import Recipient


class Notification(ABC):
    @abstractmethod
    def send(self, recipient: Recipient, message: str) -> None:
        pass
