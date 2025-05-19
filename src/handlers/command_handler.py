from datetime import datetime
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputFile
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from models.user_model import UserData
from models.message_model import MessageModel
from models.button_model import ButtonModel

from services.firebase_service import FirebaseService
from services.mercadopago_service import MercadoPagoService

messages = MessageModel()
buttons = ButtonModel()
firebase = FirebaseService()
mercado_pago = MercadoPagoService()


async def _register_user_if_needed(update: Update) -> UserData:
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


async def handle_generic_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await _register_user_if_needed(update)
    await _send_welcome_flow(update, context, user)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await _register_user_if_needed(update)
    await _send_welcome_flow(update, context, user)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _register_user_if_needed(update)
    await update.message.reply_text(
        messages.get('help'),
        parse_mode='Markdown'
    )


async def _send_welcome_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, user: dict):
    """Função compartilhada para o fluxo de boas-vindas"""
    start_msgs = messages.get('start', name=user['first_name'])

    # 1. Mensagem de boas-vindas
    await update.message.reply_text(
        start_msgs['welcome'],
        parse_mode='Markdown'
    )
    await asyncio.sleep(1.5)

    # 2. Vídeo teaser
    video_url = "https://drive.google.com/uc?id=1ra4nrjVn-etBO7vGCeZfxYSE45omnxWG"
    await context.bot.send_video(
        chat_id=update.effective_chat.id,
        video=video_url,
        caption=start_msgs['teaser'],
        parse_mode='Markdown'
    )
    await asyncio.sleep(2)

    # 3. Mensagem CTA
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=start_msgs['cta'],
        parse_mode='Markdown'
    )
    await asyncio.sleep(1)

    # 4. Mostrar planos VIP
    await _show_vip_plans(update, context)


async def _show_vip_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra os planos VIP com botões"""
    plans_msg = messages.get('vip_plans')
    plans_kb = buttons.get('vip_plans')

    if update.message:
        await update.message.reply_text(
            text=plans_msg,
            parse_mode='Markdown',
            reply_markup=plans_kb
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            text=plans_msg,
            parse_mode='Markdown',
            reply_markup=plans_kb
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Seleção de plano
    if data.startswith('plan_'):
        plan = data.split('_')[1]
        plan_names = {
            '1month': "1 MÊS - R$19.90",
            '3months': "3 MESES - R$29.90",
            '6months': "6 MESES - R$49.90",
            'lifetime': "VITALÍCIO - R$79.90"
        }
        plan_name = plan_names.get(plan, "Plano VIP")

        await query.edit_message_text(
            text=messages.get('selected_plan', plan_name=plan_name),
            parse_mode='Markdown',
            reply_markup=buttons.get('payment_methods', plan=plan)
        )

    # Seleção de método de pagamento
    elif data.startswith('payment_'):
        method, plan = data.split('_')[1], data.split('_')[2]

        if method == 'pix':
            await _process_pix_payment(query, context, plan)
        elif method == 'cc':
            await _process_credit_card(query, plan)

    # Voltar aos planos
    elif data == 'back_to_plans':
        await _show_vip_plans(update, context)

    elif data.startswith('paid_pix_'):
        plan = data.split('_')[2]
        user_id = query.from_user.id

        # Mostra mensagem de processamento
        await query.edit_message_text(
            text=messages.get('payment_pending'),
            parse_mode='Markdown'
        )

        payment_id = context.user_data.get("pix_payment_id")
        if not payment_id:
            await query.edit_message_text("❌ O pagamento PIX não foi encontrado. Por favor, tente novamente.")
            return

        await asyncio.sleep(5)

        # Simula verificação do pagamento (substitua pela lógica real)
        payment_verified, response = await _confirm_payment(
            user_id=user_id,
            plan=plan,
            payment_id=payment_id,
            payment_method='pix',
            amount={
                '1month': 19.90,
                '3months': 29.90,
                '6months': 49.90,
                'lifetime': 79.90
            }.get(plan)
        )

        # Mesmo em caso de erro ou pagamento pendente, mantemos os botões de "Já Paguei" e "Suporte"
        vip_keyboard = buttons.get('pix_confirmation_error', plan=plan)

        # Atualiza a mensagem com o resultado
        await query.edit_message_text(
            text=response,
            parse_mode='Markdown',
            reply_markup=vip_keyboard
        )


async def _process_pix_payment(query, context, plan):
    """Processa pagamento via PIX"""
    plan_prices = {
        '1month': 19.90,
        '3months': 29.90,
        '6months': 49.90,
        'lifetime': 79.90
    }
    amount = plan_prices.get(plan)

    try:
        pix_data = await mercado_pago.create_pix_payment(
            user_id=query.from_user.id,
            amount=amount,
            description=f"Plano VIP: {plan}"
        )

        context.user_data["pix_payment_id"] = pix_data["payment_id"]

        await query.edit_message_text(
            text=messages.get('pix_payment', amount=amount,
                              qr_code=pix_data['qr_code']),
            parse_mode='Markdown',
            reply_markup=buttons.get('pix_confirmation', plan=plan)
        )
    except Exception as e:
        await query.edit_message_text(
            text=messages.get('pix_error', error=str(e))
        )


async def _process_credit_card(query, plan):
    """Processa pagamento por cartão"""
    plan_prices = {
        '1month': 19.90,
        '3months': 29.90,
        '6months': 49.90,
        'lifetime': 79.90
    }
    amount = plan_prices.get(plan)

    try:
        payment_url = await mercado_pago.create_credit_card_payment_link(
            user_id=query.from_user.id,
            amount=amount,
            description=f"Plano VIP: {plan}"
        )

        await query.edit_message_text(
            text=messages.get('credit_card_payment'),
            parse_mode='Markdown',
            reply_markup=buttons.get(
                'credit_card_payment', plan=plan, payment_url=payment_url)
        )
    except Exception as e:
        await query.edit_message_text(
            text=messages.get('cc_error', error=str(e))
        )


async def _confirm_payment(user_id: int, plan: str, payment_id: str, payment_method: str, amount: float):
    """Confirma o pagamento e ativa a assinatura"""
    try:
        # Verifica o status do pagamento
        payment_status = await mercado_pago.verify_payment(payment_id)

        if payment_status != "approved":
            if payment_status == "pending":
                return False, messages.get('payment_pending')
            else:
                return False, messages.get('payment_failed')

        # Cria a assinatura no Firebase
        subscription = await firebase.create_subscription(
            user_id=user_id,
            payment_data={
                'plan': plan,
                'payment_id': payment_id,
                'method': payment_method,
                'amount': amount
            }
        )

        plan_names = {
            '1month': "1 MÊS",
            '3months': "3 MESES",
            '6months': "6 MESES",
            'lifetime': "VITALÍCIO"
        }

        success_msgs = messages.get('payment_success')
        full_message = (
            success_msgs['title'] +
            success_msgs['message'].format(
                expiration_date=subscription['expires_at'].strftime(
                    "%d/%m/%Y"),
                plan_name=plan_names.get(plan, plan)
            ) +
            "\n\n" +
            success_msgs['instructions']
        )

        return True, full_message

    except Exception as e:
        return False, messages.get('payment_failed')


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
