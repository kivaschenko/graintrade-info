from email.message import EmailMessage
from pathlib import Path
from typing import List
import os
import asyncio
import json
import aio_pika
import aiosmtplib
import logging

from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

from .database import database
from .model import get_user_by_username, get_all_users_preferences, get_category_by_id
from .schemas import PreferencesSchema, CategoryInResponse, UserInResponse
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
SMTP_HOST = os.getenv("MAILTRAP_HOST", "live.smtp.mailtrap.io")
SMTP_PORT = int(os.getenv("MAILTRAP_PORT", 587))
EMAIL_FROM = os.getenv("EMAIL_FROM")
BULK_MAILTRAP_HOST = os.getenv("BULK_MAILTRAP_HOST", "bulk.smtp.mailtrap.io")
BULK_MAILTRAP_PASS = os.getenv("BULK_MAILTRAP_PASS")
# RabbitMQ variables
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://user:password@localhost:5672/")


async def send_email(to_email, subject, body, bulk=False):
    message = EmailMessage()
    message["From"] = EMAIL_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body, subtype="html")
    if bulk:
        hostname = BULK_MAILTRAP_HOST
        password = BULK_MAILTRAP_PASS
    else:
        hostname = SMTP_HOST
        password = SMTP_PASS

    logging.info(f"Sending email to {to_email} with subject: {subject}")
    # Send the email using aiosmtplib
    await aiosmtplib.send(
        message,
        hostname=hostname,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=password,
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


async def get_users_preferences(
    category_id: int, country: str = "Ukraine"
) -> List[PreferencesSchema]:
    preferences: List[PreferencesSchema] = await get_all_users_preferences()
    category: CategoryInResponse = await get_category_by_id(category_id)
    if not category:
        return []
    users = []
    for pref in preferences:
        if not pref.interested_categories or not pref.country:
            continue
        # Check if the category and country match the user's preferences
        if category.name in pref.interested_categories and country == pref.country:
            users.append(pref)
    return users


async def handle_item_notification(msg: aio_pika.abc.AbstractIncomingMessage):
    async with msg.process():
        data = json.loads(msg.body.decode())
        print(f"Received message: {data}")
        try:
            preferences = await get_users_preferences(
                int(data["category_id"]), data["country"]
            )
            if not preferences:
                logging.info("No users found for item notifications.")
                return
            logging.info(f"Users found: {preferences}")
        except Exception as e:
            logging.error(f"Error fetching user emails: {e}")
            return
        subject = "New item created: {}".format(data["title"])
        for pref in preferences:
            user = UserInResponse(
                id=pref.user_id,  # type: ignore
                username=pref.username,  # type: ignore
                full_name=pref.full_name,
                email=pref.email,  # type: ignore
                hashed_password="mocked_password",  # Not used in email
            )
            if not user.email:
                logging.warning(f"User {user.username} has no email, skipping.")
                continue
            logging.info(f"Sending email to {user.email}")
            # Prepare the HTML body using Jinja2 template
            if not user.full_name:
                user.full_name = user.username
            html_body = env.get_template("new_item_email.html").render(
                user_name=user.full_name or user.username,
                item_title=data["title"],
                item_description=data["description"],
                item_price=data["price"],
                item_currency=data["currency"],
                item_measure=data["measure"],
                item_amount=data["amount"],
                item_country=data["country"],
                item_region=data["region"],
                item_terms_delivery=data["terms_delivery"],
                item_created_at=data["created_at"],
                item_url=f"{BASE_URL}/items/{data['id']}",
            )
            await send_email(user.email, subject, html_body)
        logging.info(f"Email sent to {user.email} with subject: {subject}")


async def main():
    rabbitmq = await get_rabbitmq_connection()
    logging.info(f"Consuming from queue: {QueueName.MESSAGE_EVENTS.value}")
    # Start consuming messages from the RabbitMQ queue
    await rabbitmq.consume(
        queue=QueueName.MESSAGE_EVENTS.value,
        callback=handle_message_notification,
    )
    # Start consuming item notifications
    logging.info(f"Consuming from queue: {QueueName.ITEM_EVENTS.value}")
    await rabbitmq.consume(
        queue=QueueName.ITEM_EVENTS.value,
        callback=handle_item_notification,
    )
    logging.info("RabbitMQ connection established and consumers started.")
    # Keep the script running to listen for messages
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
