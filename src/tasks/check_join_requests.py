import os
from telegram import Update
from telegram.ext import ContextTypes, Application, ChatJoinRequestHandler
from services.firebase_service import FirebaseService
from utils.logger import setup_logger

logger = setup_logger(__name__)


class JoinRequestProcessor:
    def __init__(self):
        self.firebase = FirebaseService()

    async def process_request(self, join_request) -> bool:
        """Processa uma solicitação de entrada e retorna se foi aprovada."""
        user = join_request.from_user
        group_id = join_request.chat.id

        logger.info(
            f"Processando solicitação de {user.id} para o grupo {group_id}")
        has_permission = await self.firebase.check_user_permission(str(user.id))

        if has_permission:
            await join_request.approve()
            logger.info(f"Aprovado: {user.id}")
        else:
            await join_request.decline()
            logger.info(f"Recusado: {user.id}")

        return has_permission


async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler principal para solicitações de entrada."""
    if not update.chat_join_request:
        logger.error("Mensagem não é uma solicitação de entrada")
        return

    processor = JoinRequestProcessor()
    try:
        await processor.process_request(update.chat_join_request)
    except Exception as e:
        logger.error(f"Erro ao processar solicitação: {e}", exc_info=True)
        try:
            await update.chat_join_request.decline()
        except Exception as decline_error:
            logger.error(f"Falha ao recusar solicitação: {decline_error}")


def setup_join_request_handler(app: Application):
    """Configura o handler de solicitações de entrada."""
    try:
        app.add_handler(ChatJoinRequestHandler(handle_join_request))
        logger.info("Handler de join requests configurado com sucesso.")
    except Exception as e:
        logger.error(
            f"Erro ao configurar join request handler: {e}", exc_info=True)
        raise
