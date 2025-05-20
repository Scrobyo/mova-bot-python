import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter
import os
from typing import Optional, List
from models.user_model import UserData
from datetime import datetime, timedelta, timezone
from utils.logger import setup_logger

logger = setup_logger("firebase_service")


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
        logger.debug(f"Buscando dados do usuário {user_id}...")
        doc = self.db.collection('users').document(str(user_id)).get()
        if doc.exists:
            logger.info(f"Usuário {user_id} encontrado.")
            return doc.to_dict()
        else:
            logger.warning(f"Usuário {user_id} não encontrado.")
            return None

    async def register_user(self, user_data: UserData) -> UserData:
        logger.info(f"Registrando novo usuário: {user_data['id']}")
        user_ref = self.db.collection('users').document(user_data['id'])
        user_ref.set(user_data)
        logger.info(f"Usuário {user_data['id']} registrado com sucesso.")
        return user_data

    async def update_user_activity(self, user_id: int):
        logger.debug(f"Atualizando atividade do usuário {user_id}")
        self.db.collection('users').document(str(user_id)).update({
            'last_activity': firestore.SERVER_TIMESTAMP
        })
        logger.debug(f"Última atividade atualizada para o usuário {user_id}")

    async def create_subscription(self, user_id: int, payment_data: dict) -> dict:
        plan = payment_data['plan']
        payment_id = payment_data.get('payment_id', 'manual')
        logger.info(
            f"Criando assinatura [{plan}] para usuário {user_id} (pagamento ID: {payment_id})")

        plan_durations = {
            '1month': timedelta(days=30),
            '3months': timedelta(days=90),
            '6months': timedelta(days=180),
            'lifetime': timedelta(days=365 * 99)
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

        self.db.collection('users').document(str(user_id)).update({
            'is_vip': True,
            'vip_expires': expires_at
        })

        sub_ref = self.db.collection('subscriptions').document()
        sub_ref.set(subscription_data)

        logger.info(
            f"Assinatura criada com sucesso para o usuário {user_id}. Expira em {expires_at.date()}.")
        return subscription_data

    async def check_and_update_vip_status(self) -> List[str]:
        logger.info("Iniciando verificação de assinaturas VIP...")
        users_ref = self.db.collection('users')
        subscriptions_ref = self.db.collection('subscriptions')
        deactivated_users = []
        now = datetime.now(timezone.utc)
        updated_subscriptions = 0

        try:
            # 1. Atualizar assinaturas expiradas
            expired_subs_query = subscriptions_ref.where(
                filter=FieldFilter('status', '==', 'active')
            ).where(
                filter=FieldFilter('expires_at', '<=', now)
            )

            expired_subs = expired_subs_query.stream()
            batch = self.db.batch()
            batch_count = 0

            for sub in expired_subs:
                sub_data = sub.to_dict()
                logger.info(
                    f"Marcando assinatura {sub.id} como expirada (User: {sub_data.get('user_id')}, Expired at: {sub_data.get('expires_at')})")

                batch.update(sub.reference, {
                    'status': 'expired',
                    'last_updated': now
                })
                batch_count += 1
                updated_subscriptions += 1

                if batch_count >= 400:
                    batch.commit()
                    logger.info(
                        f"Lote de {batch_count} assinaturas atualizadas")
                    batch = self.db.batch()
                    batch_count = 0

            if batch_count > 0:
                batch.commit()
                logger.info(
                    f"Lote final de {batch_count} assinaturas atualizadas")

            logger.info(
                f"Total de assinaturas marcadas como expiradas: {updated_subscriptions}")

            # 2. Verificar usuários VIP
            vip_users_query = users_ref.where(
                filter=FieldFilter('is_vip', '==', True)
            )
            vip_users = vip_users_query.stream()

            for user in vip_users:
                user_id = user.id
                user_data = user.to_dict()
                vip_expires = user_data.get('vip_expires')

                if vip_expires and vip_expires <= now:
                    logger.info(
                        f"Verificando usuário VIP expirado: {user_id} (Expirou em: {vip_expires})")

                    active_subs_query = subscriptions_ref.where(
                        filter=FieldFilter('user_id', '==', user_id)
                    ).where(
                        filter=FieldFilter('status', '==', 'active')
                    ).where(
                        filter=FieldFilter('expires_at', '>', now)
                    ).limit(1)

                    active_subs = list(active_subs_query.stream())

                    if not active_subs:
                        logger.info(
                            f"Removendo status VIP do usuário {user_id} (Sem assinaturas ativas)")
                        users_ref.document(user_id).update({
                            'is_vip': False,
                            'vip_expires': None
                        })
                        deactivated_users.append(user_id)
                    else:
                        logger.info(
                            f"Usuário {user_id} mantém VIP (Possui assinatura ativa até {active_subs[0].get('expires_at')})")

        except Exception as e:
            logger.error(
                f"Erro durante verificação: {str(e)}", exc_info=True)
            raise

        logger.info(
            f"Verificação concluída. Usuários desativados: {len(deactivated_users)}")
        return deactivated_users

    async def get_expiring_subscriptions(self, days_before: int = 3) -> List[dict]:
        target_date = datetime.now(timezone.utc) + timedelta(days=days_before)
        start_of_day = datetime(
            target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
        end_of_day = start_of_day + timedelta(days=1)

        logger.info(
            f"Buscando assinaturas que expiram entre {start_of_day} e {end_of_day}...")

        subscriptions = (
            self.db.collection('subscriptions')  # Corrigido o nome da coleção
            .where(filter=FieldFilter('status', '==', 'active'))
            .where(filter=FieldFilter('expires_at', '>=', start_of_day))
            .where(filter=FieldFilter('expires_at', '<', end_of_day))
            .stream()
        )

        subs_list = [sub.to_dict() for sub in subscriptions]
        logger.info(
            f"{len(subs_list)} assinaturas encontradas para expirar em {days_before} dias.")
        return subs_list

    async def check_user_permission(self, user_id: str) -> bool:
        """Verifica se o usuário tem permissão para entrar no grupo"""
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            user_doc = user_ref.get()  # Removido o await pois é síncrono

            if not user_doc.exists:
                logger.debug(f"Usuário {user_id} não encontrado")
                return False

            user_data = user_doc.to_dict()
            logger.debug(f"Dados do usuário {user_id}: {user_data}")

            # Verifica se o usuário tem VIP ativo
            is_vip = user_data.get('is_vip', False)

            # Verifica a validade do VIP (usando vip_expires que é o campo correto)
            if is_vip and 'vip_expires' in user_data:
                from datetime import datetime
                vip_expiry = user_data['vip_expires']

                # Converte para datetime se for um objeto timestamp
                if hasattr(vip_expiry, 'replace'):
                    expiry_date = vip_expiry.replace(tzinfo=None)
                else:
                    expiry_date = vip_expiry

                if datetime.now() > expiry_date:
                    logger.debug(
                        f"VIP do usuário {user_id} expirado em {expiry_date}")
                    return False

            return is_vip

        except Exception as e:
            logger.error(
                f"Erro ao verificar permissão: {str(e)}", exc_info=True)
            return False
