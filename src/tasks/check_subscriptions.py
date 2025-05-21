import asyncio
from services.firebase_service import FirebaseService
from utils.logger import setup_logger
from telegram import Bot
import os

logger = setup_logger("check_subscriptions")

# ID do grupo que você deseja monitorar (pode ser uma lista se forem vários grupos)
GROUP_ID = os.getenv("TELEGRAM_PRIVATE_GROUP_ID")  # ou um número diretamente


async def check_subscriptions(bot: Bot):
    firebase = FirebaseService()
    while True:
        try:
            logger.info("Verificando assinaturas VIP...")
            deactivated_users = await firebase.check_and_update_vip_status()
            if deactivated_users:
                logger.info(f"Usuários desativados: {deactivated_users}")
                for user_id in deactivated_users:
                    try:
                        await bot.ban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                        # Para permitir que ele volte no futuro
                        await bot.unban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                        logger.info(
                            f"Usuário {user_id} removido do grupo {GROUP_ID}")
                    except Exception as e:
                        logger.error(
                            f"Erro ao remover o usuário {user_id} do grupo: {e}")
        except Exception as e:
            logger.error(f"Erro: {e}")

        await asyncio.sleep(43200)
