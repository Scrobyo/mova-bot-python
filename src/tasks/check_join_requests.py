import asyncio
from services.firebase_service import FirebaseService
from utils.logger import setup_logger
import os
from telegram import Bot

logger = setup_logger("check_join_requests")


async def check_pending_join_requests():
    """Verifica solicitações pendentes usando uma nova instância do Bot"""
    firebase = FirebaseService()
    vip_group_id = int(os.getenv("TELEGRAM_PRIVATE_GROUP_ID"))

    # Cria uma nova instância independente do Bot
    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))

    while True:
        try:
            logger.info("Verificando solicitações de entrada pendentes...")

            # Usando a instância independente do Bot
            async with bot:
                pending_requests = await bot.get_chat_join_requests(
                    chat_id=vip_group_id
                )

                if pending_requests:
                    logger.info(
                        f"Encontradas {len(pending_requests)} solicitações pendentes")

                    for request in pending_requests:
                        user_id = request.user.id
                        logger.info(f"Processando usuário {user_id}")

                        is_vip = await firebase.is_user_vip(user_id)

                        if is_vip:
                            await bot.approve_chat_join_request(
                                chat_id=vip_group_id,
                                user_id=user_id
                            )
                            logger.info(f"Aprovado: {user_id}")
                        else:
                            await bot.decline_chat_join_request(
                                chat_id=vip_group_id,
                                user_id=user_id
                            )
                            logger.info(f"Recusado: {user_id}")

            await asyncio.sleep(60)  # Verifica a cada 5 minutos

        except Exception as e:
            logger.error(f"Erro ao verificar solicitações: {e}")
            await asyncio.sleep(600)  # Espera 10 minutos em caso de erro
