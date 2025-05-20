# bot.py

import os
import asyncio
from telegram.ext import Application
from handlers.command_handler import setup_handlers
from tasks.check_subscriptions import check_subscriptions
from tasks.check_join_requests import check_pending_join_requests
from utils.logger import setup_logger

logger = setup_logger("bot")


class BotRunner:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        if not self.token:
            raise ValueError("Token não configurado!")

        self.app = Application.builder().token(self.token).build()
        self.running = False

    async def _start_background_tasks(self):
        asyncio.create_task(check_subscriptions())
        asyncio.create_task(check_pending_join_requests())

    async def run(self):
        if self.running:
            return

        self.running = True
        setup_handlers(self.app)
        await self._start_background_tasks()
        logger.info("Bot iniciado com sucesso!")
        await self.app.run_polling()


async def run_bot():
    runner = BotRunner()
    try:
        await runner.run()
    except KeyboardInterrupt:
        logger.info("Bot encerrado pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        raise
    finally:
        logger.info("Finalizando o bot")


if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except RuntimeError as e:
        logger.error(f"Erro ao rodar o loop principal: {e}")
