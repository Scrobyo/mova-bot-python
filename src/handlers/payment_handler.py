# payment_handler.py
from datetime import datetime
import asyncio
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from typing import Tuple, Optional

from models.message_model import MessageModel
from models.button_model import ButtonModel
from services.firebase_service import FirebaseService
from services.mercadopago_service import MercadoPagoService
from utils.logger import setup_logger

logger = setup_logger(__name__)

messages = MessageModel()
buttons = ButtonModel()
firebase = FirebaseService()
mercado_pago = MercadoPagoService()


async def show_vip_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra os planos VIP com botões"""
    logger.info(
        f"Enviando planos VIP para o usuário {update.effective_user.id}")
    plans_msg = messages.get('vip_plans')
    plans_kb = buttons.get('vip_plans')

    if update.message:
        await update.message.reply_text(
            text=plans_msg,
            parse_mode='Markdown',
            reply_markup=plans_kb
        )
        logger.info("Planos VIP enviados via mensagem.")
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            text=plans_msg,
            parse_mode='Markdown',
            reply_markup=plans_kb
        )
        logger.info("Planos VIP enviados via callback query.")


async def handle_payment_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Lida com a seleção de plano ou método de pagamento"""
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
        logger.info(
            f"Usuário {query.from_user.id} selecionou o plano: {plan_name}")

        await query.edit_message_text(
            text=messages.get('selected_plan', plan_name=plan_name),
            parse_mode='Markdown',
            reply_markup=buttons.get('payment_methods', plan=plan)
        )
        return True

    # Seleção de método de pagamento
    elif data.startswith('payment_'):
        method, plan = data.split('_')[1], data.split('_')[2]
        logger.info(
            f"Usuário {query.from_user.id} selecionou o método: {method} para o plano {plan}")

        if method == 'pix':
            await process_pix_payment(query, context, plan)
            return True
        elif method == 'cc':
            await process_credit_card_payment(query, plan)
            return True

    return False


async def process_pix_payment(query, context: ContextTypes.DEFAULT_TYPE, plan: str):
    """Processa pagamento via PIX"""
    plan_prices = {
        '1month': 19.90,
        '3months': 29.90,
        '6months': 49.90,
        'lifetime': 79.90
    }
    amount = plan_prices.get(plan)

    try:
        logger.info(
            f"Processando pagamento PIX para o usuário {query.from_user.id} no plano {plan}.")

        pix_data = await mercado_pago.create_pix_payment(
            user_id=query.from_user.id,
            amount=amount,
            description=f"Plano VIP: {plan}"
        )

        context.user_data["pix_payment_id"] = pix_data["payment_id"]
        logger.info(
            f"Pagamento PIX gerado com sucesso para o usuário {query.from_user.id}. ID: {pix_data['payment_id']}")

        await query.edit_message_text(
            text=messages.get('pix_payment', amount=amount,
                              qr_code=pix_data['qr_code']),
            parse_mode='Markdown',
            reply_markup=buttons.get('pix_confirmation', plan=plan)
        )

    except Exception as e:
        logger.error(
            f"Erro ao gerar pagamento PIX para o usuário {query.from_user.id}. Erro: {str(e)}")
        await query.edit_message_text(text=messages.get('pix_error', error=str(e)))


async def process_credit_card_payment(query, plan: str):
    """Processa pagamento por cartão"""
    plan_prices = {
        '1month': 19.90,
        '3months': 29.90,
        '6months': 49.90,
        'lifetime': 79.90
    }
    amount = plan_prices.get(plan)

    try:
        logger.info(
            f"Iniciando pagamento por cartão de crédito para o usuário {query.from_user.id}, plano: {plan}.")

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
        logger.error(
            f"Erro ao gerar link de pagamento por cartão de crédito para o usuário {query.from_user.id}. Erro: {str(e)}")
        await query.edit_message_text(text=messages.get('cc_error', error=str(e)))


async def handle_pix_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Tuple[bool, Optional[str]]:
    """Lida com a confirmação de pagamento PIX"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if not data.startswith('paid_pix_'):
        return False, None

    plan = data.split('_')[2]
    user_id = query.from_user.id

    # Mostra mensagem de processamento
    await query.edit_message_text(
        text=messages.get('payment_pending'),
        parse_mode='Markdown'
    )

    payment_id = context.user_data.get("pix_payment_id")
    if not payment_id:
        logger.error(
            f"Pagamento PIX não encontrado para o usuário {user_id}.")
        await query.edit_message_text("O pagamento PIX não foi encontrado. Por favor, tente novamente.")
        return True, None

    # Verificação REAL do pagamento
    logger.info(
        f"Iniciando a verificação do pagamento PIX para o usuário {user_id}.")
    payment_verified, response, vip_buttons = await confirm_payment(
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

    if payment_verified:
        logger.info(f"Pagamento PIX aprovado para o usuário {user_id}.")
        await query.edit_message_text(
            text=response,
            parse_mode='Markdown',
            reply_markup=vip_buttons
        )
    else:
        logger.warning(
            f"Pagamento PIX para o usuário {user_id} falhou ou está pendente.")
        vip_keyboard = buttons.get('pix_confirmation_error', plan=plan)
        await query.edit_message_text(
            text=response,
            parse_mode='Markdown',
            reply_markup=vip_keyboard
        )

    return True, None


async def confirm_payment(user_id: int, plan: str, payment_id: str, payment_method: str, amount: float) -> Tuple[bool, str, Optional[InlineKeyboardMarkup]]:
    """Confirma o pagamento e ativa a assinatura"""
    try:
        logger.info(
            f"Verificando pagamento {payment_id} para o usuário {user_id}...")

        payment_status = await mercado_pago.verify_payment(payment_id)
        logger.info(f"Status do pagamento {payment_id}: {payment_status}")

        if payment_status != "approved":
            if payment_status == "pending":
                return False, messages.get('payment_pending'), None
            else:
                return False, messages.get('payment_failed'), None

        logger.info(
            f"Pagamento aprovado para o usuário {user_id}. Criando assinatura...")
        subscription = await firebase.create_subscription(
            user_id=user_id,
            payment_data={
                'plan': plan,
                'payment_id': payment_id,
                'method': payment_method,
                'amount': amount
            }
        )

        if not subscription or 'expires_at' not in subscription:
            logger.error(
                f"Erro: Assinatura não criada corretamente para o usuário {user_id}.")
            return False, messages.get('payment_failed'), None

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
            )
        )

        return True, full_message, buttons.get('vip_success')

    except Exception as e:
        logger.error(
            f"Erro ao confirmar pagamento {payment_id} para o usuário {user_id}. Erro: {str(e)}")
        return False, messages.get('payment_failed'), None
