import logging
import os
from fastapi import APIRouter, HTTPException
from .schemas import Recipient, Notification
from ..service_layer.notification_services import (
    EmailNotificationHandler,
    SMSNotificationHandler,
    TelegramNotificationHandler,
    WhatsAppNotificationHandler,
    # NotificationService,
)

JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("JWT_EXPIRES_IN")

router = APIRouter(tags=["notification"])

HANDLERS = {
    "email": EmailNotificationHandler,
    "sms": SMSNotificationHandler,
    "telegram": TelegramNotificationHandler,
    "whatsapp": WhatsAppNotificationHandler,
}

logger = logging.getLogger("app_logger")


@router.post("/notify")
async def notify(notification: Notification):
    recipient = Recipient(**notification.recipient)
    message = notification.message
    method = notification.method

    logger.info(f"Received notification request: {notification}")

    if method not in HANDLERS:
        logger.error(f"Invalid notification method: {method}")
        raise HTTPException(status_code=400, detail="Invalid notification method")

    handler = HANDLERS[method]
    await handler.send(recipient, message)
    logger.info(f"Notification sent successfully to {recipient} via {method}")
    return {"message": "Notification sent successfully"}
