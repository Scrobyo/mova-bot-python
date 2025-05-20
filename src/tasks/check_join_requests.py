# tasks/check_join_requests.py
import os
from telegram import Update
from telegram.ext import ContextTypes, Application, ChatJoinRequestHandler
from services.firebase_service import FirebaseService
from utils.logger import setup_logger

logger = setup_logger("check_join_requests")


async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.chat_join_request:
            logger.error("Mensagem não é uma solicitação de entrada")
            return

        join_request = update.chat_join_request
        user = join_request.from_user
        group_id = join_request.chat.id

        logger.info(
            f"Processando solicitação de {user.id} para o grupo {group_id}")

        # Inicializa o FirebaseService
        firebase = FirebaseService()

        # Verifica permissão (note que check_user_permission é assíncrono)
        has_permission = await firebase.check_user_permission(str(user.id))

        if has_permission:
            await join_request.approve()
            logger.info(f"Aprovado: {user.id}")
        else:
            await join_request.decline()
            logger.info(f"Recusado: {user.id}")

    except Exception as e:
        logger.error(f"Erro fatal: {e}", exc_info=True)
        try:
            await join_request.decline()
        except:
            pass


def setup_join_request_handler(app: Application):
    try:
        handler = ChatJoinRequestHandler(handle_join_request)
        app.add_handler(handler)
        logger.info("Handler de join requests configurado com sucesso.")
    except Exception as e:
        logger.error(
            f"Erro ao configurar join request handler: {str(e)}", exc_info=True)
