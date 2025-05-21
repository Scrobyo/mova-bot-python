# main.py
import os
import asyncio
from telegram.ext import Application
from handlers.command_handler import setup_handlers
from tasks.check_subscriptions import check_subscriptions
from tasks.check_join_requests import setup_join_request_handler  # Corrigido
from utils.logger import setup_logger

logger = setup_logger("bot")


# main.py

def run_bot():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("Token não configurado!")

    app = Application.builder().token(token).build()

    # Configura comandos e handlers
    setup_handlers(app)
    setup_join_request_handler(app)

    # Inicia tarefas assíncronas
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.create_task(check_subscriptions(app.bot))  # Passe o bot aqui
        logger.info("Bot iniciado com sucesso!")
        app.run_polling()
    finally:
        loop.close()
