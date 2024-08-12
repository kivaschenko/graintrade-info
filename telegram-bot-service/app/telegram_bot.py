import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from fastapi import FastAPI
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
AUTH_API_URL = "http://localhost:8001"
ITEM_API_URL = "http://localhost:8002"

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hi! Use /login <username> <password> to log in.')

def login(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 2:
        update.message.reply_text('Usage: /login <username> <password>')
        return

    username, password = context.args
    response = requests.post(f"{AUTH_API_URL}/token", data={"username": username, "password": password})
    if response.status_code == 200:
        token = response.json().get("access_token")
        context.user_data["token"] = token
        update.message.reply_text('Logged in successfully!')
    else:
        update.message.reply_text('Login failed!')

def create_item(update: Update, context: CallbackContext) -> None:
    if "token" not in context.user_data:
        update.message.reply_text('You need to log in first using /login <username> <password>')
        return

    if len(context.args) != 1:
        update.message.reply_text('Usage: /create_item <title>')
        return

    title = context.args[0]
    token = context.user_data["token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{ITEM_API_URL}/items/", headers=headers, json={"title": title})
    if response.status_code == 200:
        update.message.reply_text('Item created successfully!')
    else:
        update.message.reply_text('Failed to create item!')

def main() -> None:
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("login", login))
    dispatcher.add_handler(CommandHandler("create_item", create_item))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()