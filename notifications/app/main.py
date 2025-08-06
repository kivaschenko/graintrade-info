from email.message import EmailMessage
from pathlib import Path
from typing import Dict, List
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
from .services import get_all_users_by_topic_preferences

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
# Mailtrap SMTP Configuration for Transactional Emails
TRANSACTIONAL_SMTP_USER = os.getenv("TRANSACTIONAL_MAILTRAP_USER")
TRANSACTIONAL_SMTP_PASS = os.getenv("TRANSACTIONAL_MAILTRAP_PASS")
TRANSACTIONAL_SMTP_HOST = os.getenv("TRANSACTIONAL_MAILTRAP_HOST")
TRANSACTIONAL_SMTP_PORT = int(os.getenv("TRANSACTIONAL_MAILTRAP_PORT", 587))
EMAIL_FROM = os.getenv("EMAIL_FROM")
# Mailtrap SMTP Configuration for Notification Emails
BULK_MAILTRAP_HOST = os.getenv("BULK_MAILTRAP_HOST")
BULK_MAILTRAP_PORT = int(os.getenv("BULK_MAILTRAP_PORT", 587))
BULK_MAILTRAP_USER = os.getenv("BULK_MAILTRAP_USER")
BULK_MAILTRAP_PASS = os.getenv("BULK_MAILTRAP_PASS")
# RabbitMQ variables
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://user:password@localhost:5672/")

# ------------------------------
# Messages handling for RabbitMQ


async def send_email(to_email, subject, body):
    """Send an email using Mailtrap SMTP server. For transactional emails."""
    message = EmailMessage()
    message["From"] = f"Graintrade.Info <{EMAIL_FROM}>"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=TRANSACTIONAL_SMTP_HOST,
        port=TRANSACTIONAL_SMTP_PORT,
        username=TRANSACTIONAL_SMTP_USER,
        password=TRANSACTIONAL_SMTP_PASS,
        start_tls=True,
    )


async def handle_message_notification(msg: aio_pika.abc.AbstractIncomingMessage):
    async with msg.process():
        data = json.loads(msg.body.decode())
        if data["type"] == "new_message":
            try:
                user = await get_user_by_username(data["to_username"])
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


# ----------------------------
# Topics handling for RabbitMQ


async def send_bulk_email(to_email: str, subject: str, body: str):
    """Send bulk email using Mailtrap SMTP server."""
    message = EmailMessage()
    message["From"] = f"Graintrade.Info <{EMAIL_FROM}>"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=BULK_MAILTRAP_HOST,
        port=BULK_MAILTRAP_PORT,
        username=BULK_MAILTRAP_USER,
        password=BULK_MAILTRAP_PASS,
        start_tls=True,
    )


async def send_emails_about_message_notifications():
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
    rabbitmq = loop.run_until_complete(send_emails_about_message_notifications())
    logging.info("Connected to RabbitMQ.")
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(rabbitmq.close())
        loop.run_until_complete(database.disconnect())
        loop.close()
        logging.info("Notification service stopped.")
