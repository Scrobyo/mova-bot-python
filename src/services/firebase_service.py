import firebase_admin
from firebase_admin import credentials, firestore
from telegram import User as TelegramUser
import os
from typing import Optional
from models.user_model import UserData
from datetime import datetime, timedelta


class FirebaseService:
    def __init__(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate({
                "type": os.getenv("FIREBASE_TYPE"),
                "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
                "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
                "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
                "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
            })
            firebase_admin.initialize_app(cred)

        self.db = firestore.client()

    async def get_user(self, user_id: int) -> Optional[UserData]:
        doc = self.db.collection('users').document(str(user_id)).get()
        return doc.to_dict() if doc.exists else None

    async def register_user(self, user_data: UserData) -> UserData:
        user_ref = self.db.collection('users').document(user_data['id'])
        user_ref.set(user_data)
        return user_data

    async def update_user_activity(self, user_id: int):
        self.db.collection('users').document(str(user_id)).update({
            'last_activity': firestore.SERVER_TIMESTAMP
        })

    async def create_subscription(self, user_id: int, payment_data: dict) -> dict:
        """Cria uma assinatura VIP para o usuário"""
        plan = payment_data['plan']
        payment_id = payment_data.get('payment_id', 'manual')

        # Calcula a data de expiração baseada no plano
        plan_durations = {
            '1month': timedelta(days=30),
            '3months': timedelta(days=90),
            '6months': timedelta(days=180),
            'lifetime': timedelta(days=365*99)  # 99 anos para "vitalício"
        }

        expires_at = datetime.now() + plan_durations.get(plan, timedelta(days=30))

        subscription_data = {
            'user_id': str(user_id),
            'plan': plan,
            'payment_id': payment_id,
            'payment_method': payment_data.get('method', 'pix'),
            'amount': payment_data.get('amount', 0),
            'status': 'active',
            'created_at': datetime.now(),
            'expires_at': expires_at,
            'last_updated': datetime.now()
        }

        # Atualiza o status do usuário para VIP
        await self.db.collection('users').document(str(user_id)).update({
            'is_vip': True,
            'vip_expires': expires_at
        })

        # Cria o documento na coleção de assinaturas
        sub_ref = self.db.collection('subscriptions').document()
        sub_ref.set(subscription_data)

        return subscription_data
