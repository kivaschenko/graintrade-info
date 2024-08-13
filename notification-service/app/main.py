from fastapi import FastAPI, HTTPException
from .schemas import Recipient, Notification
from .services import (
    EmailNotificationHandler,
    SMSNotificationHandler,
    TelegramNotificationHandler,
    # NotificationService,
)


app = FastAPI()

HANDLERS = {
    "email": EmailNotificationHandler,
    "sms": SMSNotificationHandler,
    "telegram": TelegramNotificationHandler,
}


@app.post("/notify")
async def notify(notification: Notification):
    recipient = Recipient(**notification.recipient)
    message = notification.message
    method = notification.method

    if method not in HANDLERS:
        raise HTTPException(status_code=400, detail="Invalid notification method")

    handler = HANDLERS[method]
    await handler.send(recipient, message)
    return {"message": "Notification sent successfully"}