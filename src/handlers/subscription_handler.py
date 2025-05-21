import os
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from typing import Optional

from models.message_model import MessageModel
from services.firebase_service import FirebaseService
from utils.logger import setup_logger

logger = setup_logger(__name__)

messages = MessageModel()
firebase = FirebaseService()

# Obtém o ID do grupo VIP do ambiente
VIP_GROUP_ID = os.getenv("TELEGRAM_PRIVATE_GROUP_ID")


async def is_user_vip(user_id: int) -> bool:
    """Verifica se o usuário tem assinatura VIP ativa"""
    try:
        logger.info(f"Verificando status VIP do usuário {user_id}")
        user_data = await firebase.get_user(str(user_id))

        if not user_data:
            return False

        # Verifica se é VIP e se a assinatura não expirou
        if user_data.get('is_vip', False):
            expires = user_data.get('vip_expires')
            if expires and expires > datetime.now():
                return True
        return False
    except Exception as e:
        logger.error(
            f"Erro ao verificar status VIP do usuário {user_id}: {str(e)}")
        return False


async def handle_group_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa solicitações de entrada no grupo VIP"""
    if not update.message or not update.message.new_chat_members:
        return

    for user in update.message.new_chat_members:
        user_id = user.id
        logger.info(f"Processando entrada do usuário {user_id} no grupo VIP")

        is_vip = await is_user_vip(user_id)

        if is_vip:
            try:
                # Aprova a entrada do usuário
                await context.bot.approve_chat_join_request(
                    chat_id=VIP_GROUP_ID,
                    user_id=user_id
                )
                logger.info(f"Usuário {user_id} aprovado no grupo VIP")

                # Mensagem de boas-vindas no privado
                await context.bot.send_message(
                    chat_id=user_id,
                    text=messages.get('vip_group_welcome'),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Falha ao aprovar usuário {user_id}: {str(e)}")
        else:
            try:
                # Recusa a entrada do usuário
                await context.bot.decline_chat_join_request(
                    chat_id=VIP_GROUP_ID,
                    user_id=user_id
                )
                logger.info(f"Usuário {user_id} recusado no grupo VIP")

                # Mensagem explicativa no privado
                await context.bot.send_message(
                    chat_id=user_id,
                    text=messages.get('vip_group_denied'),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Falha ao recusar usuário {user_id}: {str(e)}")


def setup_handlers(app):
    # Handler para solicitações de entrada no grupo
    app.add_handler(MessageHandler(
        filters.Chat(VIP_GROUP_ID) & filters.StatusUpdate.NEW_CHAT_MEMBERS,
        handle_group_join_request
    ))

    logger.info("Subscription handlers configurados")
