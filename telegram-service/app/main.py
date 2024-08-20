# telegram_bot.py
# Description: This file contains the code for the Telegram bot service.
from pathlib import Path
import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackContext,
)
import requests
from dotenv import load_dotenv

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
AUTH_API_URL = "http://172.22.0.1:8001"
ITEM_API_URL = "http://172.22.0.1:8002"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hi! Use /login <username> <password> to log in.\n Use /items to get items.",
    )


async def get_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # if "token" not in context.user_data:
    #     await update.message.reply_text("You need to log in first using /login <username> <password>")
    #     return

    # token = context.user_data["token"]
    # headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{ITEM_API_URL}/items/",
        # headers=headers
    )
    if response.status_code == 200:
        items = response.json()
        if items:
            message = []
            for item in items:
                message.append(
                    f"<a href='#'><b>{item['title']}</b></a>\n"
                    f"<code>{item['description']}</code>\n"
                    f"<i>Price: </i><code>{item['price']} {item['currency']}</code>\n"
                    f"<i>Amount: </i><code>{item['amount']} {item['measure']}</code>\n"
                    f"<i>Incoterms: </i><code>{item['terms_delivery']} {item['country']} {item['region']}</code>\n"
                    f"<i>Created at: </i><code>{item['created_at']}</code>\n"
                    "=================\n")
            await update.message.reply_text(
                "\tItems:\n\n" + "\n".join(message), parse_mode="HTML"
            )
        else:
            await update.message.reply_text("No items found!")
    else:
        await update.message.reply_text("Failed to get items!")


async def login(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /login <username> <password>")
        return

    username, password = context.args
    response = requests.post(
        f"{AUTH_API_URL}/token", data={"username": username, "password": password}
    )
    if response.status_code == 200:
        token = response.json().get("access_token")
        context.user_data["token"] = token
        update.message.reply_text("Logged in successfully!")
    else:
        update.message.reply_text("Login failed!")


def create_item(update: Update, context: CallbackContext) -> None:
    if "token" not in context.user_data:
        update.message.reply_text(
            "You need to log in first using /login <username> <password>"
        )
        return

    if len(context.args) != 1:
        update.message.reply_text("Usage: /create_item <title>")
        return

    title = context.args[0]
    token = context.user_data["token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{ITEM_API_URL}/items/", headers=headers, json={"title": title}
    )
    if response.status_code == 200:
        update.message.reply_text("Item created successfully!")
    else:
        update.message.reply_text("Failed to create item!")


def main() -> None:
    apllication = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    start_handler = CommandHandler("start", start)
    login_handler = CommandHandler("login", login)
    create_item_handler = CommandHandler("create_item", create_item)
    items_handler = CommandHandler("items", get_items)

    apllication.add_handler(start_handler)
    apllication.add_handler(items_handler)
    apllication.add_handler(login_handler)
    apllication.add_handler(create_item_handler)

    apllication.run_polling()


if __name__ == "__main__":
    main()
