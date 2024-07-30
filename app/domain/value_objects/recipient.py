from dataclasses import dataclass
from typing import Optional


@dataclass
class Recipient:
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    telegram_id: Optional[str] = None
