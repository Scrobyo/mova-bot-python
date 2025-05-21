import asyncio
from services.firebase_service import FirebaseService
from utils.logger import setup_logger
from telegram import Bot
import os

logger = setup_logger(__name__)


class SubscriptionManager:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.firebase = FirebaseService()
        self.group_id = os.getenv("TELEGRAM_PRIVATE_GROUP_ID")
        self.running = True

    async def remove_expired_users(self, user_ids: list):
        """Remove usuários expirados do grupo."""
        for user_id in user_ids:
            try:
                await self.bot.ban_chat_member(chat_id=self.group_id, user_id=user_id)
                await self.bot.unban_chat_member(chat_id=self.group_id, user_id=user_id)
                logger.info(f"Usuário {user_id} removido do grupo")
            except Exception as e:
                logger.error(f"Erro ao remover usuário {user_id}: {e}")

    async def stop(self):
        """Para a verificação de assinaturas."""
        self.running = False

    async def check_subscriptions(self):
        """Verifica periodicamente o status das assinaturas."""
        while self.running:
            try:
                logger.info("Verificando assinaturas VIP...")
                deactivated_users = await self.firebase.check_and_update_vip_status()

                if deactivated_users:
                    logger.info(f"Usuários desativados: {deactivated_users}")
                    await self.remove_expired_users(deactivated_users)

            except Exception as e:
                logger.error(f"Erro na verificação de assinaturas: {e}")

            await asyncio.sleep(43200)  # 12 horas


async def check_subscriptions(bot: Bot):
    """Ponto de entrada para a tarefa de verificação de assinaturas."""
    manager = SubscriptionManager(bot)
    await manager.check_subscriptions()
