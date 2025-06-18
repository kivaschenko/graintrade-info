from sqlalchemy.orm import Session
from . import models, schemas


def create_message(db: Session, item_id: str, sender_id: str, content: str):
    db_message = models.Message(item_id=item_id, sender_id=sender_id, content=content)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_messages(db: Session, item_id: str, limit: int = 50):
    return (
        db.query(models.Message)
        .filter(models.Message.item_id == item_id)
        .order_by(models.Message.timestamp.asc())
        .limit(limit)
        .all()
    )
