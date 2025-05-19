import os
from telegram.ext import Application
from handlers.command_handler import setup_handlers


def start_bot():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("Token não configurado!")

    app = Application.builder().token(token).build()
    setup_handlers(app)

    print("🤖 Bot iniciado com sucesso!")
    app.run_polling()
