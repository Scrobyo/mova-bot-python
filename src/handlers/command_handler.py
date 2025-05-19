import datetime
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputFile
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from models.user_model import UserData
from models.message_model import MessageModel
from models.button_model import ButtonModel

from services.firebase_service import FirebaseService

firebase = FirebaseService()
messages = MessageModel()
buttons = ButtonModel()


async def _register_user_if_needed(update: Update) -> UserData:
    """Centraliza o registro/atualização de usuários"""
    user = update.effective_user
    user_data = await firebase.get_user(user.id)

    if not user_data:
        new_user: UserData = {
            'id': str(user.id),
            'first_name': user.first_name,
            'last_name': user.last_name or '',
            'username': user.username or '',
            'language_code': user.language_code or 'pt-br',
            'is_bot': user.is_bot,
            'created_at': datetime.datetime.now(),
            'last_activity': datetime.datetime.now(),
            'is_vip': False,
            'vip_expires': None
        }
        return await firebase.register_user(new_user)

    await firebase.update_user_activity(user.id)
    return user_data


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await _register_user_if_needed(update)
    first_name = user['first_name']

    start_messages = messages.get('start', name=first_name)

    # Parte 1: Mensagem de boas-vindas
    await update.message.reply_text(
        start_messages['welcome'],
        parse_mode='Markdown'
    )
    await asyncio.sleep(1.5)

    # Parte 2: Video teaser
    video_url = "https://drive.google.com/uc?id=1ra4nrjVn-etBO7vGCeZfxYSE45omnxWG"
    await context.bot.send_video(
        chat_id=update.effective_chat.id,
        video=video_url,
        caption=start_messages['teaser'],
        parse_mode='Markdown'
    )
    await asyncio.sleep(2)

    # Parte 3: Mensagem CTA (sem botões)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=start_messages['cta'],
        parse_mode='Markdown'
    )
    await asyncio.sleep(1)

    # Parte 4: Mensagem de seleção COM botões VIP
    plans_message, plans_keyboard = buttons.get('vip_plans')
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=plans_message,
        parse_mode='Markdown',
        reply_markup=plans_keyboard
    )


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _register_user_if_needed(update)
    await update.message.reply_text(
        messages.get('help'),
        parse_mode='Markdown'
    )


async def handle_generic_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await _register_user_if_needed(update)
    await update.message.reply_text(
        messages.get('start', name=user['first_name']),
        parse_mode='Markdown'
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # Handler para seleção de planos
    if data.startswith('plan_'):
        plan = data.split('_')[1]
        plan_name = {
            '1month': "1 MÊS - R$19.90",
            '3months': "3 MESES - R$29.90",
            '6months': "6 MESES - R$49.90",
            'lifetime': "VITALÍCIO - R$79.90"
        }.get(plan, "Plano VIP")

        # Mostra opções de pagamento para o plano selecionado
        payment_msg, payment_kb = buttons.get(
            'payment_methods',
            plan=plan
        )

        await query.edit_message_text(
            text=f"🎯 *PLANO SELECIONADO:* {plan_name}\n\n{payment_msg}",
            parse_mode='Markdown',
            reply_markup=payment_kb
        )

    # Handler para seleção de pagamento
    elif data.startswith('payment_'):
        method, plan = data.split('_')[1], data.split('_')[2]

        if method == 'pix':
            await process_pix_payment(query, plan)
        elif method == 'cc':
            await process_credit_card(query, plan)

    # Handler para voltar aos planos
    elif data == 'back_to_plans':
        plans_msg, plans_kb = buttons.get('vip_plans')
        await query.edit_message_text(
            text=plans_msg,
            parse_mode='Markdown',
            reply_markup=plans_kb
        )


async def process_pix_payment(query, plan):
    """Lógica específica para pagamento via PIX"""
    values = {
        '1month': "19.90",
        '3months': "29.90",
        '6months': "49.90",
        'lifetime': "79.90"
    }

    await query.edit_message_text(
        text=f"🔹 *PAGAMENTO VIA PIX* 🔹\n\n"
        f"Valor: R$ {values.get(plan)}\n"
        f"Chave: 123.456.789-00\n\n"
        f"Envie o comprovante para @suporte",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "✅ JÁ PAGUEI", callback_data=f"paid_pix_{plan}")],
            [InlineKeyboardButton("↩️ VOLTAR", callback_data=f"plan_{plan}")]
        ])
    )


async def process_credit_card(query, plan):
    """Lógica específica para cartão de crédito"""
    await query.edit_message_text(
        text=f"🚀 *PAGAMENTO POR CARTÃO* 🚀\n\n"
        f"Clique no botão abaixo para pagar com segurança:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔒 PAGAR COM CARTÃO",
                                  url="https://seusite.com/checkout")],
            [InlineKeyboardButton("↩️ VOLTAR", callback_data=f"plan_{plan}")]
        ])
    )


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
