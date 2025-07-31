from sqlalchemy import Column, Integer, String, DateTime
from .database import Base
import datetime


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(String, index=True)  # items.uuid
    sender_id = Column(String, index=True)  # users.username
    receiver_id = Column(String, index=True)  # users.username
    content = Column(String)  # message text
    timestamp = Column(
        DateTime, default=datetime.datetime.now(tz=datetime.timezone.utc)
    )
