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

            """
            Message in RabbitMQ example:
            {
                "type": "commodity_prices_weekly", 
                "timestamp": "2025-10-19T15:53:55.816860", 
                "data": {
                    "telegram_message": "📆 *Тижневий дайджест зернового ринку* — 19.10.2025\n💱 USD→UAH: 41.72\n\n🌍 *Світові біржові котирування (ф'ючерси CBOT):*\n\n• *Пшениця*\n  5.04 USD/bushel | 185.10 USD/т | 7722 ₴/т\n• *Кукурудза*\n  4.22 USD/bushel | 166.33 USD/т | 6939 ₴/т\n• *Соя*\n  10.20 USD/bushel | 374.60 USD/т | 15628 ₴/т\n• *Овес*\n  2.95 USD/bushel | 203.24 USD/т | 8479 ₴/т\n• *Рис*\n  10.69 USD/cwt | 235.67 USD/т | 9832 ₴/т\n\n📊 *ETF (біржові фонди):*\n• Пшениця (ETF): $4.05 (169 ₴)\n• Кукурудза (ETF): $17.54 (732 ₴)\n• Соя (ETF): $21.82 (910 ₴)\n• Аграрний кошик (ETF): $26.54 (1107 ₴)\n• Цукор (ETF): $9.89 (413 ₴)\n\n🏢 *Акції аграрних компаній:*\n• Archer-Daniels-Midland (аграрна компанія): $63.33 (2642 ₴)\n• Bunge Limited (аграрна компанія): $97.50 (4068 ₴)\n• Tyson Foods (м'ясна компанія): $52.48 (2189 ₴)\n• Mosaic Company (добрива): $29.32 (1223 ₴)\n\nℹ️ *Пояснення для трейдерів:*\n• Ф'ючерси CBOT котируються в центах за бушель або cwt (100 фунтів)\n• Конверсія: бушель→тонна залежить від культури (різна вага)\n• Базис між світовою та українською ціною враховує логістику\n• ETF — фінансовий інструмент, не пряма ціна фізичного товару\n• EXW = франко-завод, FOB = франко-борт, CPT = перевезення оплачено\n\n🕐 Оновлено: 15:53 19.10.2025\n🔎 Джерела: Yahoo Finance (ф'ючерси CBOT, ETF, акції компаній)", "usd_uah_rate": 41.72, 
                    "commodities": [{"name": "Wheat Futures", "ticker": "ZW=F", "category": "futures", "raw_price": 503.75, "price_in_dollars": 5.0375, "unit": "bushel", "usd_per_ton": 185.0967279675185, "uah_per_ton": 7722.235490804871, "usd_per_share": NaN, "uah_per_share": NaN, "description": "Пшениця (ф'ючерс CBOT)", "note": "ф'ючерсний контракт"}, {"name": "Corn Futures", "ticker": "ZC=F", "category": "futures", "raw_price": 422.5, "price_in_dollars": 4.225, "unit": "bushel", "usd_per_ton": 166.33072453269924, "uah_per_ton": 6939.317827504212, "usd_per_share": NaN, "uah_per_share": NaN, "description": "Кукурудза (ф'ючерс CBOT)", "note": "ф'ючерсний контракт"}, {"name": "Soybeans Futures", "ticker": "ZS=F", "category": "futures", "raw_price": 1019.5, "price_in_dollars": 10.195, "unit": "bushel", "usd_per_ton": 374.60270801565287, "uah_per_ton": 15628.424978413037, "usd_per_share": NaN, "uah_per_share": NaN, "description": "Соя (ф'ючерс CBOT)", "note": "ф'ючерсний контракт"}, {"name": "Oats Futures", "ticker": "ZO=F", "category": "futures", "raw_price": 295.0, "price_in_dollars": 2.95, "unit": "bushel", "usd_per_ton": 203.23802962452635, "uah_per_ton": 8479.090595935239, "usd_per_share": NaN, "uah_per_share": NaN, "description": "Овес (ф'ючерс CBOT)", "note": "ф'ючерсний контракт"}, {"name": "Rough Rice Futures", "ticker": "ZR=F", "category": "futures", "raw_price": 1069.0, "price_in_dollars": 10.69, "unit": "cwt", "usd_per_ton": 235.6741582756341, "uah_per_ton": 9832.325883259455, "usd_per_share": NaN, "uah_per_share": NaN, "description": "Рис (ф'ючерс CBOT)", "note": "ф'ючерсний контракт"}, {"name": "Wheat ETF", "ticker": "WEAT", "category": "etf", "raw_price": 4.050000190734863, "price_in_dollars": 4.050000190734863, "unit": "share", "usd_per_ton": NaN, "uah_per_ton": NaN, "usd_per_share": 4.050000190734863, "uah_per_share": 168.9660079574585, "description": "Пшениця (ETF)", "note": "ETF/акція"}, {"name": "Corn ETF", "ticker": "CORN", "category": "etf", "raw_price": 17.540000915527344, "price_in_dollars": 17.540000915527344, "unit": "share", "usd_per_ton": NaN, "uah_per_ton": NaN, "usd_per_share": 17.540000915527344, "uah_per_share": 731.7688381958008, "description": "Кукурудза (ETF)", "note": "ETF/акція"}, {"name": "Soybeans ETF", "ticker": "SOYB", "category": "etf", "raw_price": 21.81999969482422, "price_in_dollars": 21.81999969482422, "unit": "share", "usd_per_ton": NaN, "uah_per_ton": NaN, "usd_per_share": 21.81999969482422, "uah_per_share": 910.3303872680664, "description": "Соя (ETF)", "note": "ETF/акція"}, {"name": "Agricultural Basket", "ticker": "DBA", "category": "etf", "raw_price": 26.540000915527344, "price_in_dollars": 26.540000915527344, "unit": "share", "usd_per_ton": NaN, "uah_per_ton": NaN, "usd_per_share": 26.540000915527344, "uah_per_share": 1107.2488381958008, "description": "Аграрний кошик (ETF)", "note": "ETF/акція"}, {"name": "Sugar ETF", "ticker": "CANE", "category": "etf", "raw_price": 9.890000343322754, "price_in_dollars": 9.890000343322754, "unit": "share", "usd_per_ton": NaN, "uah_per_ton": NaN, "usd_per_share": 9.890000343322754, "uah_per_share": 412.6108143234253, "description": "Цукор (ETF)", "note": "ETF/акція"}, {"name": "Coffee ETF", "ticker": "JO", "category": "etf", "raw_price": NaN, "price_in_dollars": NaN, "unit": "share", "usd_per_ton": NaN, "uah_per_ton": NaN, "usd_per_share": NaN, "uah_per_share": NaN, "description": "Кава (ETF)", "note": "дані недоступні"}, {"name": "ADM", "ticker": "ADM", "category": "company", "raw_price": 63.33000183105469, "price_in_dollars": 63.33000183105469, "unit": "share", "usd_per_ton": NaN, "uah_per_ton": NaN, "usd_per_share": 63.33000183105469, "uah_per_share": 2642.1276763916017, "description": "Archer-Daniels-Midland (аграрна компанія)", "note": "акція компанії"}, {"name": "Bunge", "ticker": "BG", "category": "company", "raw_price": 97.5, "price_in_dollars": 97.5, "unit": "share", "usd_per_ton": NaN, "uah_per_ton": NaN, "usd_per_share": 97.5, "uah_per_share": 4067.7, "description": "Bunge Limited (аграрна компанія)", "note": "акція компанії"}, {"name": "Tyson Foods", "ticker": "TSN", "category": "company", "raw_price": 52.47999954223633, "price_in_dollars": 52.47999954223633, "unit": "share", "usd_per_ton": NaN, "uah_per_ton": NaN, "usd_per_share": 52.47999954223633, "uah_per_share": 2189.4655809020996, "description": "Tyson Foods (м'ясна компанія)", "note": "акція компанії"}, {"name": "Mosaic (Fertilizer)", "ticker": "MOS", "category": "company", "raw_price": 29.31999969482422, "price_in_dollars": 29.31999969482422, "unit": "share", "usd_per_ton": NaN, "uah_per_ton": NaN, "usd_per_share": 29.31999969482422, "uah_per_share": 1223.2303872680664, "description": "Mosaic Company (добрива)", "note": "акція компанії"}], "ukrainian_prices": null}, 
                "destination": "telegram_channel"}
            """
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
