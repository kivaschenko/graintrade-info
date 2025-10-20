from typing import List
import json
import logging
import aio_pika
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from .model import (
    get_user_by_username,
    get_user_by_id,
    get_all_users_preferences,
    get_category_by_id,
    get_user_subscritpion_by_order_id,
)
from .schemas import PreferencesSchema, CategoryInResponse, UserInResponse

# Import environment variables
from .config import (
    BASE_URL,
    TELEGRAM_CHANNEL_ID,
    ENABLE_EMAIL,
    ENABLE_TELEGRAM,
    ENABLE_VIBER,
)
from .channels.email import send_email
from .channels.telegram_ptb import send_telegram_message
from .channels.viber import send_viber_message
from .model import create_item_telegram_message_id
from .channels.telegram_ptb import delete_telegram_message

BASE_DIR = Path(__file__).resolve().parent.parent
env = Environment(loader=FileSystemLoader(BASE_DIR / "app" / "templates"))

OFFER_TYPES_UA = {"sell": "Продаю", "buy": "Купую"}


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
        elif (
            data["type"] == "commodity_prices_daily"
            or data["type"] == "commodity_prices_weekly"
        ):
            # Currently no action needed for commodity price notifications
            logging.info(
                f"Received commodity price notification of type: {data['type']}"
            )

            # check destination channels if needed
            if (
                data.get("destination") == "telegram_channel"
                and ENABLE_TELEGRAM
                and TELEGRAM_CHANNEL_ID
            ):
                # Extract telegram_message from nested data structure
                message_data = data.get("data", {})
                tg_text = message_data.get("telegram_message", "")
                if tg_text:
                    message = await send_telegram_message(TELEGRAM_CHANNEL_ID, tg_text)
                    if message:
                        logging.info(
                            f"Commodity prices message sent to Telegram channel {TELEGRAM_CHANNEL_ID}"
                        )
                    else:
                        logging.error(
                            "Failed to send commodity prices message to Telegram."
                        )
                else:
                    logging.warning(
                        "No telegram_message content found in the notification data."
                    )
        else:
            return


async def get_users_preferences(
    category_id: int, country: str = "Ukraine"
) -> List[PreferencesSchema]:
    preferences: List[PreferencesSchema] = await get_all_users_preferences()
    category: CategoryInResponse = await get_category_by_id(category_id)  # type: ignore
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
        # Data for item notifications: {'id': '63', 'uuid': '1667dc20-333f-48a0-98e5-4e351d5eeca3', 'category_id': '15',
        # 'offer_type': 'sell', 'title': 'Продаю Гречка', 'description': 'без сміття, чиста',
        # 'price': '34500.0', 'currency': 'UAH', 'amount': '230', 'measure': 'metric ton',
        # 'terms_delivery': 'FCA', 'country': 'Ukraine', 'region': 'Cherkasy Oblast',
        # 'latitude': '49.675243', 'longitude': '32.034566',
        # 'created_at': '2025-09-06 11:52:41.205496',
        # 'owner_id': 'None', 'category': 'None', 'user_id': '6',
        # 'category_name': 'Buckwheat', 'category_ua_name': 'Гречка'}
        item_id = int(data["id"])
        offer_type = data.get("offer_type")
        ua_offer_type = OFFER_TYPES_UA.get(offer_type)
        en_offer_type = offer_type.capitalize()
        ua_title = f"{ua_offer_type} #{data.get('category_ua_name')}"
        en_title = f"{en_offer_type} #{data.get('category_name')}"
        if ENABLE_TELEGRAM and TELEGRAM_CHANNEL_ID:
            item_url = f"{BASE_URL}/items/{item_id}"
            type_icon = "🟢" if offer_type == "sell" else "🔴"
            description = (data.get("description") or "—").strip()
            if len(description) > 300:
                description = description[:297] + "..."
            tg_text = (
                f"{type_icon} <b>{ua_title} ({en_title})</b>\n\n"
                f"💰 <b>Ціна (Price):</b> {data.get('price')} {data.get('currency')}\n"
                f"📦 <b>Кількість (Amount):</b> {data.get('amount')} {data.get('measure')}\n"
                f"📍 <b>Місце (Point):</b> {data.get('country')}{', ' + data.get('region') if data.get('region') else ''}\n"
                f"🚚 <b>Умови (Incoterms):</b> {data.get('terms_delivery', '—')}\n"
                f"📝 <b>Опис (Description):</b> description\n\n"
                f'➡️ <a href="{item_url}">Детальніше (Details)</a>'
            )
            message = await send_telegram_message(TELEGRAM_CHANNEL_ID, tg_text)
            if not message:
                logging.error("Failed to send Telegram message.")
                return
            message_id = message.message_id
            chat = message.chat
            if message and chat:
                await create_item_telegram_message_id(item_id, message_id, chat.id)
                logging.info(f"Telegram message sent to channel {TELEGRAM_CHANNEL_ID}")
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
        if ENABLE_EMAIL:
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
                # Choose template according language of notifications
                if pref.language == "ua":
                    template_name = "ua_new_item_email.html"
                    subject = "New item created: {}".format(data["title"])
                    html_body = env.get_template(template_name).render(
                        user_name=user.full_name or user.username,
                        item_title=ua_title,
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
                else:
                    template_name = "new_item_email.html"
                    subject = "Нова пропозиція створена: {}".format(data["title"])
                    html_body = env.get_template(template_name).render(
                        user_name=user.full_name or user.username,
                        item_title=en_title,
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
        # Viber broadcast to users (if you have IDs)
        if ENABLE_VIBER:
            viber_text = (
                f"🆕 Новий товар!\n"
                f"{data['title']}\n"
                f"Ціна: {data.get('price')} {data.get('currency')}\n"
                f"Деталі: {BASE_URL}/items/{data['id']}"
            )
            print("Viber text:", viber_text)
            # Example: if you collect viber_ids in DB
            # for pref in preferences: await send_viber_message(pref.viber_id, viber_text)


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


async def handle_deleted_item_notification(
    msg: aio_pika.abc.AbstractIncomingMessage,
):
    async with msg.process():
        data = json.loads(msg.body.decode())
        item_id = int(data["id"])
        telegram_message_id = int(data.get("telegram_message_id", 0))
        chat_id = int(data.get("chat_id", 0))
        if ENABLE_TELEGRAM and TELEGRAM_CHANNEL_ID:
            if not telegram_message_id:
                logging.warning(
                    f"No telegram message found for item ID: {item_id} (cannot delete)"
                )
                return
            if not chat_id:
                logging.warning(
                    f"Chat id missing for stored telegram message {telegram_message_id} (item {item_id})"
                )
                return
            deleted = await delete_telegram_message(
                chat_id=chat_id, message_id=telegram_message_id
            )
            if deleted is False:
                logging.error(
                    f"Failed to delete Telegram message {telegram_message_id} in chat {chat_id}"
                )
            else:
                logging.info(
                    f"Telegram message {telegram_message_id} in chat {chat_id} deleted successfully"
                )


async def handle_user_registration_notification(
    msg: aio_pika.abc.AbstractIncomingMessage,
):
    """
    Handle new user registration notifications.
    Sends a welcome email to the new user in both English and Ukrainian.

    Expected data format:
    {
        "username": "maximus",
        "email": "max@example.com",
        "full_name": "Max Cat",
        "phone": "",
        "disabled": "False",
        "hashed_password": "$2b$12$...",
        "id": "9"
    }
    """
    async with msg.process():
        data = json.loads(msg.body.decode())

        if not ENABLE_EMAIL:
            logging.info("Email notifications are disabled, skipping welcome email")
            return

        try:
            email = data.get("email")
            username = data.get("username")
            full_name = data.get("full_name") or username

            if not email:
                logging.warning(
                    f"No email provided for user {username}, skipping welcome email"
                )
                return

            # Send English version
            subject_en = "Welcome to GrainTrade Info! 🌾"
            html_body_en = env.get_template("welcome_email_en.html").render(
                user_name=full_name
            )
            await send_email(email, subject_en, html_body_en)
            logging.info(f"Welcome email (EN) sent to {email}")

            # Send Ukrainian version
            subject_ua = "Ласкаво просимо до GrainTrade Info! 🌾"
            html_body_ua = env.get_template("welcome_email_ua.html").render(
                user_name=full_name
            )
            await send_email(email, subject_ua, html_body_ua)
            logging.info(f"Welcome email (UA) sent to {email}")

        except Exception as e:
            logging.error(f"Error processing user registration notification: {e}")
