from email.message import EmailMessage
from pathlib import Path
import os
import asyncio
import json
import aio_pika
import aiosmtplib
import logging

from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

from .database import database
from .model import get_user_by_username
from .rabbit_mq import QueueName, get_rabbitmq_connection

BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
BASE_DIR = Path(__file__).resolve().parent.parent
env = Environment(loader=FileSystemLoader(BASE_DIR / "app" / "templates"))
# Load environment variables
if not BASE_DIR.joinpath(".env").exists():
    raise FileNotFoundError("Environment file .env not found in the base directory.")
else:
    logging.info("Loading environment variables from .env file.")
load_dotenv(BASE_DIR / ".env")

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
    message.set_content(body, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=SMTP_PASS,
        start_tls=True,
    )


async def handle_message_notification(msg: aio_pika.abc.AbstractIncomingMessage):
    async with msg.process():
        data = json.loads(msg.body.decode())
        print(f"Received message: {data}")
        if data["type"] == "new_message":
            try:
                user = await get_user_by_username(data["to_username"])
                print(f"User found: {user}")
            except Exception as e:
                logging.error(f"Error fetching user or item: {e}")
                return
            subject = "You have a new message"
            # body = f"You received a new message: {data['message_text']}\nView item: {BASE_URL}/items/{data['item_id']}"
            # await send_email(user.email, subject, body)
            html_body = env.get_template("new_message_email.html").render(
                user_name=user.full_name or user.username,
                message_text=data["message_text"],
                item_url=f"{BASE_URL}/items/{data['item_id']}",
            )
            await send_email(user.email, subject, html_body)
            logging.info(f"Email sent to {user.email} with subject: {subject}")
        else:
            return


async def main():
    rabbitmq = await get_rabbitmq_connection()
    logging.info(f"Consuming from queue: {QueueName.MESSAGE_EVENTS.value}")
    # Start consuming messages from the RabbitMQ queue
    await rabbitmq.consume(
        queue=QueueName.MESSAGE_EVENTS.value,
        callback=handle_message_notification,
    )
    print("Waiting for notifications...")
    return rabbitmq


if __name__ == "__main__":
    logging.info("Starting notification service...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(database.connect())
    logging.info("Connected to database and Redis.")
    logging.info("Connecting to RabbitMQ...")
    rabbitmq = loop.run_until_complete(main())
    logging.info("Connected to RabbitMQ.")
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(rabbitmq.close())
        loop.run_until_complete(database.disconnect())
        loop.close()
        logging.info("Notification service stopped.")
