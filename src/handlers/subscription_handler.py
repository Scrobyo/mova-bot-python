import os
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from services.firebase_service import FirebaseService
from utils.logger import setup_logger

logger = setup_logger("subscription-handler")

firebase = FirebaseService()
VIP_GROUP_ID = os.getenv("TELEGRAM_PRIVATE_GROUP_ID")


async def handle_group_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa solicitações de entrada no grupo VIP em tempo real"""
    if not update.message or not update.message.new_chat_members:
        return

    for user in update.message.new_chat_members:
        user_id = user.id
        logger.info(
            f"Processando entrada do usuário {user_id} no grupo VIP (tempo real)")

        is_vip = await firebase.is_user_vip(user_id)

        if is_vip:
            try:
                await context.bot.approve_chat_join_request(
                    chat_id=VIP_GROUP_ID,
                    user_id=user_id
                )
                logger.info(f"Usuário {user_id} aprovado (tempo real)")
            except Exception as e:
                logger.error(f"Falha ao aprovar usuário {user_id}: {str(e)}")
        else:
            try:
                await context.bot.decline_chat_join_request(
                    chat_id=VIP_GROUP_ID,
                    user_id=user_id
                )
                logger.info(f"Usuário {user_id} recusado (tempo real)")
            except Exception as e:
                logger.error(f"Falha ao recusar usuário {user_id}: {str(e)}")


def setup_handlers(app):
    app.add_handler(MessageHandler(
        filters.Chat(VIP_GROUP_ID) & filters.StatusUpdate.NEW_CHAT_MEMBERS,
        handle_group_join_request
    ))
    logger.info("Subscription handlers configurados")
