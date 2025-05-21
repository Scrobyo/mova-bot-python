# command_handler.py
from datetime import datetime
import asyncio
from telegram import Update, InputFile
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from models.user_model import UserData
from models.message_model import MessageModel
from services.firebase_service import FirebaseService
from utils.logger import setup_logger

# Import dos novos handlers
from handlers.payment_handler import (
    show_vip_plans,
    handle_payment_selection,
    handle_pix_confirmation
)

# Log setup
logger = setup_logger(__name__)

messages = MessageModel()
firebase = FirebaseService()


async def _register_user_if_needed(update: Update) -> UserData:
    user = update.effective_user
    logger.info(
        f"Iniciando registro do usuário {user.id} - {user.first_name} {user.last_name or ''}.")

    user_data = await firebase.get_user(user.id)

    if not user_data:
        logger.info(
            f"Usuário {user.id} não encontrado. Criando novo usuário no Firebase.")
        new_user: UserData = {
            'id': str(user.id),
            'first_name': user.first_name,
            'last_name': user.last_name or '',
            'username': user.username or '',
            'language_code': user.language_code or 'pt-br',
            'is_bot': user.is_bot,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'is_vip': False,
            'vip_expires': None
        }
        registered_user = await firebase.register_user(new_user)
        logger.info(f"Usuário {user.id} registrado com sucesso.")
        return registered_user

    logger.info(
        f"Usuário {user.id} encontrado, atualizando última atividade.")
    await firebase.update_user_activity(user.id)
    return user_data


async def handle_generic_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Mensagem recebida de {update.effective_user.id}")
    user = await _register_user_if_needed(update)
    await _send_welcome_flow(update, context, user)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(
        f"Iniciando fluxo de boas-vindas para o usuário {update.effective_user.id}")
    user = await _register_user_if_needed(update)
    await _send_welcome_flow(update, context, user)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Usuário {update.effective_user.id} solicitou ajuda.")
    await _register_user_if_needed(update)
    await update.message.reply_text(
        messages.get('help'),
        parse_mode='Markdown'
    )


async def _send_welcome_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, user: dict):
    """Função compartilhada para o fluxo de boas-vindas"""
    logger.info(
        f"Enviando fluxo de boas-vindas para o usuário {user['id']} - {user['first_name']}")

    start_msgs = messages.get('start', name=user['first_name'])

    # 1. Mensagem de boas-vindas
    welcome_msg = start_msgs['welcome'].format(name=user['first_name'])
    await update.message.reply_text(
        welcome_msg,
        parse_mode='Markdown'
    )
    logger.info(f"Mensagem de boas-vindas enviada para {user['first_name']}")

    await asyncio.sleep(1.5)

    # 2. Vídeo teaser
    video_url = "https://drive.google.com/uc?id=1ra4nrjVn-etBO7vGCeZfxYSE45omnxWG"
    await context.bot.send_video(
        chat_id=update.effective_chat.id,
        video=video_url,
        caption=start_msgs['teaser'],
        parse_mode='Markdown'
    )
    logger.info("Teaser enviado para o usuário.")
    await asyncio.sleep(2)

    # 3. Mensagem CTA
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=start_msgs['cta'],
        parse_mode='Markdown'
    )
    logger.info("Mensagem de call-to-action enviada.")
    await asyncio.sleep(1)

    # 4. Mostrar planos VIP (usando a função do payment_handler)
    await show_vip_plans(update, context)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Primeiro tenta lidar com pagamentos
    handled = await handle_payment_selection(update, context)
    if handled:
        return

    # Depois tenta lidar com confirmação PIX
    handled, _ = await handle_pix_confirmation(update, context)
    if handled:
        return

    # Voltar aos planos
    if data == 'back_to_plans':
        logger.info(f"↩Usuário {query.from_user.id} voltou aos planos VIP.")
        await show_vip_plans(update, context)


def setup_handlers(app):
    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ajuda", help))

    # Callbacks de botões
    app.add_handler(CallbackQueryHandler(button_callback))

    # Mensagens genéricas
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_generic_message
    ))

    # Fallback
    app.add_handler(MessageHandler(
        filters.COMMAND,
        lambda update, ctx: update.message.reply_text(
            messages.get('unknown_command'))
    ))

    logger.info("Handlers configurados corretamente.")
