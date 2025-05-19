import asyncio
from services.firebase_service import FirebaseService
from utils.logger import setup_logger

logger = setup_logger("check_subscriptions")


async def check_subscriptions():
    firebase = FirebaseService()
    while True:
        try:
            logger.info("🔍 Verificando assinaturas VIP...")
            deactivated_users = await firebase.check_and_update_vip_status()
            if deactivated_users:
                logger.info(f"➖ Usuários desativados: {deactivated_users}")
        except Exception as e:
            logger.error(f"❌ Erro: {e}")

        await asyncio.sleep(43200)
