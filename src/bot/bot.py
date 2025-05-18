from telegram.ext import Application
from .handlers import setup_handlers
import os


def start_bot():
    token = os.getenv("TELEGRAM_TOKEN")
    application = Application.builder().token(token).build()

    setup_handlers(application)

    print("Bot está rodando...")
    application.run_polling()
