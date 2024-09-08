from pydantic import BaseModel
from typing import Optional


class Notification(BaseModel):
    recipient: str
    message: str
    method: str  # 'email', 'sms', 'telegram'


class Recipient(BaseModel):
    email: Optional[str]
    phone: Optional[str]
    telegram_id: Optional[str]
    device_id: Optional[str]
    viber_id: Optional[str]
