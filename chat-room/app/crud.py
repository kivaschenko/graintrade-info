from sqlalchemy.orm import Session
from . import models, schemas


def create_message(
    db: Session, item_id: str, sender_id: str, receiver_id: str, content: str
):
    db_message = models.Message(
        item_id=item_id, sender_id=sender_id, receiver_id=receiver_id, content=content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_messages_between_users(
    db: Session, item_id: str, user1: str, user2: str, limit: int = 50
):
    return (
        db.query(models.Message)
        .filter(models.Message.item_id == item_id)
        .filter(
            (
                (models.Message.sender_id == user1)
                & (models.Message.receiver_id == user2)
            )
            | (
                (models.Message.sender_id == user2)
                & (models.Message.receiver_id == user1)
            )
        )
        .order_by(models.Message.timestamp.asc())
        .limit(limit)
        .all()
    )


def get_chat_participants(db: Session, item_id: str):
    rows = (
        db.query(models.Message.sender_id)
        .filter(models.Message.item_id == item_id)
        .distinct()
        .all()
    )
    print(f"Rows: {rows}")
    return [{"id": row[0], "username": row[0]} for row in rows if row[0]]
