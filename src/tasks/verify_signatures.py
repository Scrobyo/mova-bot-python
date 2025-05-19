import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import List

from services.firebase_service import FirebaseService
# Você precisará implementar isso
from bot.bot import send_expiration_notification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SignatureVerifier:
    def __init__(self):
        self.firebase = FirebaseService()

    async def verify_and_notify(self) -> List[str]:
        """Verifica assinaturas expiradas e notifica usuários"""
        logger.info("Iniciando verificação de assinaturas...")

        # 1. Verifica e atualiza status VIP
        deactivated_users = await self.firebase.check_and_update_vip_status()

        # 2. Notifica usuários (implemente conforme seu bot)
        for user_id in deactivated_users:
            try:
                await send_expiration_notification(user_id)
                logger.info(f"Notificado usuário {user_id}")
            except Exception as e:
                logger.error(f"Erro ao notificar {user_id}: {str(e)}")

        logger.info(
            f"Verificação concluída. {len(deactivated_users)} usuários desativados.")
        return deactivated_users


async def main():
    verifier = SignatureVerifier()
    await verifier.verify_and_notify()


def run_scheduled_task():
    """Configura o agendamento diário"""
    while True:
        now = datetime.now()
        target_time = time(12, 0)  # Meio-dia

        if now.time() >= target_time:
            logger.info("Executando verificação de assinaturas...")
            asyncio.run(main())

            # Espera até amanhã para evitar múltiplas execuções
            tomorrow = now + timedelta(days=1)
            tomorrow_target = datetime.combine(tomorrow.date(), target_time)
            sleep_seconds = (tomorrow_target - now).total_seconds()
            time.sleep(sleep_seconds)
        else:
            # Espera 1 minuto antes de verificar novamente
            time.sleep(60)


if __name__ == "__main__":
    run_scheduled_task()
