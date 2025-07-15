<BS>import asyncio
import json
import aio_pika
from email.message import EmailMessage
import aiosmtplib
import os
from jinja2 import Template

# Load environment (Mailtrap)
SMTP_USER = os.getenv("MAILTRAP_USER")
SMTP_PASS = os.getenv("MAILTRAP_PASS")
SMTP_HOST = os.getenv("MAILTRAP_HOST", "smtp.mailtrap.io")
SMTP_PORT = int(os.getenv("MAILTRAP_PORT", 587))
EMAIL_FROM = os.getenv("EMAIL_FROM", "no-reply@example.com")
# RabbitMQ variables
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://user:password@localhost:5672/")

async def send_email(to_email, subject, body):
    message = EmailMessage()
    message["From"] = EMAIL_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=SMTP_PASS,
        start_tls=True,
    )

async def handle_notification(msg: aio_pika.IncomingMessage):
    async with msg.process():
        data = json.loads(msg.body.decode())
        user_email = lookup_user_email(data["to_user_id"])  # You write this function to query DB

        if data["type"] == "new_message":
            subject = "You have a new message"
            body = f"You received a new message: {data['message_text']}\nView item: /items/{data['item_id']}"
        elif data["type"] == "new_item":
            subject = f"New item in {data['category']}: {data['item_title']}"
            body = f"A new item '{data['item_title']}' was added.\nCheck it here: /items/{data['item_id']}"
        else:
            return

        await send_email(user_email, subject, body)

async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue("notifications.email")

    await queue.consume(handle_notification)
    print("Waiting for notifications...")

    return connection

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    connection = loop.run_until_complete(main())
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(connection.close())

