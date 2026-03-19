from pydantic import BaseModel
from datetime import datetime


class MessageBase(BaseModel):
    item_id: str
    sender_id: str
    content: str


class MessageCreate(MessageBase):
    pass


class MessageOut(MessageBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True
