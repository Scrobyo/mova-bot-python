import os
import mercadopago
from datetime import datetime, timedelta
from typing import Dict, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MercadoPagoService:
    def __init__(self):
        access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
        if not access_token:
            raise ValueError("MERCADOPAGO_ACCESS_TOKEN não está definido!")

        self.sdk = mercadopago.SDK(access_token)
        logger.info("Mercado Pago SDK conectado com sucesso ⚡")

    async def create_pix_payment(
        self,
        user_id: int,
        amount: float,
        description: str = "Assinatura VIP"
    ) -> Dict:
        expiration_hours = 24
        expiration_date = (datetime.now() + timedelta(hours=expiration_hours)
                           ).strftime("%Y-%m-%dT%H:%M:%S.000-03:00")

        payment_data = {
            "transaction_amount": amount,
            "description": description,
            "payment_method_id": "pix",
            "payer": {
                "email": f"user_{user_id}@noemail.com",
                "first_name": "Cliente",
                "last_name": f"ID: {user_id}",
            },
            "date_of_expiration": expiration_date,
        }

        try:
            logger.info(
                f"Gerando pagamento PIX | Usuário: {user_id} | Valor: R${amount:.2f}")
            payment = self.sdk.payment().create(payment_data)
            if payment["status"] != 201:
                error_msg = payment["response"].get(
                    "message", "Erro desconhecido")
                logger.error(f"Erro ao criar PIX: {error_msg}")
                raise Exception(f"Erro ao criar PIX: {error_msg}")

            logger.info(
                f"PIX gerado com sucesso | ID do pagamento: {payment['response']['id']}")
            return {
                "qr_code": payment["response"]["point_of_interaction"]["transaction_data"]["qr_code"],
                "qr_code_base64": payment["response"]["point_of_interaction"]["transaction_data"]["qr_code_base64"],
                "amount": amount,
                "expiration_date": expiration_date,
                "payment_id": payment["response"]["id"],
            }

        except Exception as e:
            logger.error(
                f"Falha ao gerar PIX | Usuário: {user_id} | Erro: {str(e)}")
            raise

    async def create_credit_card_payment_link(
        self,
        user_id: int,
        amount: float,
        description: str = "Assinatura VIP",
        success_url: Optional[str] = None,
        failure_url: Optional[str] = None,
    ) -> str:
        preference_data = {
            "items": [
                {
                    "title": description,
                    "quantity": 1,
                    "unit_price": amount,
                }
            ],
            "payer": {
                "email": f"user_{user_id}@noemail.com",
            },
            "auto_return": "approved",
            "back_urls": {
                "success": success_url or "https://t.me/seubot",
                "failure": failure_url or "https://t.me/seubot",
            },
            "notification_url": None,
        }

        try:
            logger.info(
                f"Criando link de pagamento (cartão) | Usuário: {user_id} | Valor: R${amount:.2f}")
            preference = self.sdk.preference().create(preference_data)
            if preference["status"] != 201:
                error_msg = preference["response"].get(
                    "message", "Erro desconhecido")
                logger.error(f"Erro ao criar link de pagamento: {error_msg}")
                raise Exception(f"Erro ao criar link: {error_msg}")

            logger.info(
                f"Link de pagamento criado com sucesso | Usuário: {user_id}")
            return preference["response"]["init_point"]

        except Exception as e:
            logger.error(
                f"Erro ao gerar link de cartão | Usuário: {user_id} | Erro: {e}")
            raise

    async def verify_payment(self, payment_id: str) -> str:
        try:
            logger.info(f"Verificando pagamento | ID: {payment_id}")
            payment = self.sdk.payment().get(payment_id)
            status = payment["response"].get("status")
            logger.info(f"Status do pagamento {payment_id}: {status}")
            return status or "unknown"
        except Exception as e:
            logger.error(f"Erro ao verificar pagamento {payment_id}: {e}")
            return "error"
