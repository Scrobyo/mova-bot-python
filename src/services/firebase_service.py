import firebase_admin
from firebase_admin import credentials, firestore
from telegram import User as TelegramUser
import os
from typing import Optional
from models.user_model import UserData
from datetime import datetime


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
