import logging
from services.firebase_service import FirebaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_signatures():
    try:
        firebase = FirebaseService()
        logger.info("🔍 Verificando assinaturas VIP...")
        deactivated_users = await firebase.check_and_update_vip_status()

        if deactivated_users:
            logger.info(f"➖ Usuários desativados: {deactivated_users}")
        else:
            logger.info("✅ Nenhuma assinatura expirada encontrada.")
    except Exception as e:
        logger.error(f"❌ Erro na verificação: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(verify_signatures())
