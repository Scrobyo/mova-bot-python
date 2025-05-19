import os
import mercadopago
from datetime import datetime, timedelta
from typing import Dict, Optional


class MercadoPagoService:
    def __init__(self):
        # Configura as credenciais do Mercado Pago (usando variáveis de ambiente)
        access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
        if not access_token:
            raise ValueError("🚨 MERCADOPAGO_ACCESS_TOKEN não está definido!")

        self.sdk = mercadopago.SDK(access_token)

    async def create_pix_payment(
        self,
        user_id: int,
        amount: float,
        description: str = "Assinatura VIP"
    ) -> Dict:
        """
        Cria um pagamento via PIX com data de expiração formatada corretamente.
        """
        expiration_hours = 24  # PIX expira em 24 horas
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
            "date_of_expiration": expiration_date,  # Formato corrigido
        }

        try:
            payment = self.sdk.payment().create(payment_data)
            if payment["status"] != 201:
                error_msg = payment["response"].get(
                    "message", "Erro desconhecido")
                raise Exception(f"Erro ao criar PIX: {error_msg}")

            return {
                "qr_code": payment["response"]["point_of_interaction"]["transaction_data"]["qr_code"],
                "qr_code_base64": payment["response"]["point_of_interaction"]["transaction_data"]["qr_code_base64"],
                "amount": amount,
                "expiration_date": expiration_date,
                "payment_id": payment["response"]["id"],
            }
        except Exception as e:
            raise Exception(f"Falha ao gerar PIX: {str(e)}")

    async def create_credit_card_payment_link(
        self,
        user_id: int,
        amount: float,
        description: str = "Assinatura VIP",
        success_url: Optional[str] = None,
        failure_url: Optional[str] = None,
    ) -> str:
        """
        Cria um link de checkout para cartão de crédito (sem webhook).
        """
        preference_data = {
            "items": [
                {
                    "title": description,
                    "quantity": 1,
                    "unit_price": amount,
                }
            ],
            "payer": {
                "email": f"user_{user_id}@noemail.com",  # Obrigatório
            },
            "auto_return": "approved",  # Redireciona após pagamento
            "back_urls": {
                "success": success_url or "https://t.me/seubot",  # URL de fallback
                "failure": failure_url or "https://t.me/seubot",
            },
            "notification_url": None,  # Sem webhook
        }

        try:
            preference = self.sdk.preference().create(preference_data)
            if preference["status"] != 201:
                raise Exception(
                    f"Erro ao criar link: {preference['response'].get('message')}")

            return preference["response"]["init_point"]  # URL de pagamento

        except Exception as e:
            raise Exception(f"Falha ao gerar link: {str(e)}")

    async def verify_payment(self, payment_id: str) -> bool:
        """
        Verifica se o pagamento foi aprovado no Mercado Pago.
        """
        try:
            payment = self.sdk.payment().get(payment_id)
            status = payment["response"].get("status")

            # Opcional: printar ou logar o status
            print(f"Status do pagamento {payment_id}: {status}")

            return status == "approved"
        except Exception as e:
            print(f"Erro ao verificar pagamento: {e}")
            return False
