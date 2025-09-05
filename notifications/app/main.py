from email.message import EmailMessage
from typing import List
from pathlib import Path
import os
import asyncio
import json
import aio_pika
import aiosmtplib
import logging

from jinja2 import Environment, FileSystemLoader

from .database import database
from .model import (
    get_user_by_username,
    get_user_by_id,
    get_all_users_preferences,
    get_category_by_id,
    get_user_subscritpion_by_order_id,
)
from .schemas import PreferencesSchema, CategoryInResponse, UserInResponse
from .rabbit_mq import QueueName, get_rabbitmq_connection
from .channels.email import send_email
from .channels.telegram_ptb import send_telegram_message
from .channels.viber import send_viber_message

# Import environment variables
from .config import (
    BASE_URL,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASS,
    EMAIL_FROM,
    BULK_MAILTRAP_HOST,
    BULK_MAILTRAP_PASS,
    RABBITMQ_URL,
    TELEGRAM_CHANNEL_ID,
    ENABLE_EMAIL,
    ENABLE_TELEGRAM,
    ENABLE_VIBER,
)

BASE_DIR = Path(__file__).resolve().parent.parent
env = Environment(loader=FileSystemLoader(BASE_DIR / "templates"))


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


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

        # Telegram broadcast
        if ENABLE_TELEGRAM and TELEGRAM_CHANNEL_ID:
            tg_text = (
                f"🆕 <b>{data['title']}</b>\n"
                f"{data.get('description', 'Опис відсутній')}\n\n"
                f"💰 <b>Ціна:</b> {data.get('price')} {data.get('currency')} | {data.get('amount')} {data.get('measure')}\n"
                f"📍 <b>Місце:</b> {data.get('country')}{', ' + data.get('region') if data.get('region') else ''}\n"
                f"🚚 <b>Умови (Incoterms):</b> {data.get('terms_delivery', '—')}\n\n"
                f"➡️ <a href='{BASE_URL}/items/{data['id']}'>Детальніше</a>"
            )
            await send_telegram_message(TELEGRAM_CHANNEL_ID, tg_text)

        # Viber broadcast to users (if you have IDs)
        if ENABLE_VIBER:
            viber_text = (
                f"🆕 Новий товар!\n"
                f"{data['title']}\n"
                f"Ціна: {data.get('price')} {data.get('currency')}\n"
                f"Деталі: {BASE_URL}/items/{data['id']}"
            )
            # Example: if you collect viber_ids in DB
            # for pref in preferences: await send_viber_message(pref.viber_id, viber_text)
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
            # TODO: check language of notifications and make flow to separate templates
            # Prepare subject for email
            subject = "New item created: {}".format(data["title"])
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


async def handle_payment_notification(msg: aio_pika.abc.AbstractIncomingMessage):
    async with msg.process():
        data = json.loads(msg.body.decode())
        try:
            user_subscription = await get_user_subscritpion_by_order_id(
                data["order_id"]
            )
            if not user_subscription:
                logging.warning(
                    f"No subscription found for order ID: {data['order_id']}"
                )
                return
            user = await get_user_by_id(user_id=user_subscription.user_id)
            if not user.email:
                logging.warning(f"User {user.username} has no email, skipping.")
                return
            subject = "Payment Confirmation"
            html_body = env.get_template("payment_confirmation_email.html").render(
                user_name=user.full_name or user.username,
                order_id=data["order_id"],
                amount=data["amount"] / 100,  # Assuming amount is in cents
                currency=data["currency"],
                status=data["response_status"],
                subscription_details=f"{user_subscription.tarif.name} - {user_subscription.tarif.price} {user_subscription.tarif.currency}",  # type: ignore
            )
            await send_email(to_email=user.email, subject=subject, body_html=html_body)
            logging.info(f"Payment confirmation email sent to {user.email}")
        except Exception as e:
            logging.error(f"Error processing payment notification: {e}")


async def handle_password_recovery_notification(
    msg: aio_pika.abc.AbstractIncomingMessage,
):
    async with msg.process():
        data = json.loads(msg.body.decode())
        print(data)

        try:
            subject = "Password Recovery"
            html_body = env.get_template("password_recovery_email.html").render(
                user_name=data["full_name"] or data["username"],
                recovery_url=data["recovery_url"],
            )
            await send_email(data["email"], subject, html_body)
            logging.info(f"Password recovery email sent to {data['email']}")
        except Exception as e:
            logging.error(f"Error processing password recovery notification: {e}")


async def main():
    rabbitmq = await get_rabbitmq_connection()
    logging.info("RabbitMQ connection established and consumers started.")
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
    # Start consuming payment notifications
    logging.info(f"Consuming from queue: {QueueName.PAYMENT_EVENTS.value}")
    await rabbitmq.consume(
        queue=QueueName.PAYMENT_EVENTS.value,
        callback=handle_payment_notification,
    )

    # Start consuming password recovery notifications
    logging.info(f"Consuming from queue: {QueueName.RECOVERY_EVENTS.value}")
    await rabbitmq.consume(
        queue=QueueName.RECOVERY_EVENTS.value,
        callback=handle_password_recovery_notification,
    )

    # Keep the script running to listen for messages
    logging.info("Waiting for notifications...")
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
    except KeyboardInterrupt:
        logging.info("Shutting down notification service...")
    finally:
        loop.run_until_complete(rabbitmq.close())
        loop.run_until_complete(database.disconnect())
        loop.close()
        logging.info("Notification service stopped.")
