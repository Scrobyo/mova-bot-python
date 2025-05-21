import os
import asyncio
from telegram.ext import Application
from handlers.command_handler import setup_handlers
from tasks.check_subscriptions import check_subscriptions
from tasks.check_join_requests import setup_join_request_handler
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BotRunner:
    def __init__(self):
        self.app = None
        self.background_task = None

    async def setup_background_tasks(self):
        """Configura tarefas em segundo plano."""
        self.background_task = asyncio.create_task(
            check_subscriptions(self.app.bot))

    def create_application(self) -> Application:
        """Factory para criar a aplicação do Telegram."""
        token = os.getenv("TELEGRAM_TOKEN")
        if not token:
            raise ValueError("Token não configurado!")
        return Application.builder().token(token).build()

    async def run(self):
        """Função principal para iniciar o bot."""
        self.app = self.create_application()

        # Configura handlers
        setup_handlers(self.app)
        setup_join_request_handler(self.app)

        # Configura tarefas em segundo plano
        await self.setup_background_tasks()

        logger.info("Bot iniciado com sucesso!")
        try:
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()

            # Mantém o bot rodando até ser interrompido
            while True:
                await asyncio.sleep(3600)

        except asyncio.CancelledError:
            logger.info("Recebido sinal de cancelamento")
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Encerra o bot de forma limpa."""
        if self.background_task:
            self.background_task.cancel()
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass

        if self.app:
            if self.app.updater:
                await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
        logger.info("Bot encerrado com sucesso")
