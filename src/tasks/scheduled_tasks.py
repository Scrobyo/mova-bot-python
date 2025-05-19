# tasks/scheduled_tasks.py
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from services.firebase_service import FirebaseService
from datetime import datetime

firebase = FirebaseService()


async def check_and_update_subscriptions():
    """Tarefa agendada para verificar e atualizar status VIP"""
    print(f"⏳ [{datetime.now()}] Verificando assinaturas expiradas...")

    try:
        deactivated = await firebase.check_and_update_vip_status()
        if deactivated:
            print(f"✅ {len(deactivated)} usuários desativados: {deactivated}")
        else:
            print("✅ Nenhum usuário precisou ser desativado.")

    except Exception as e:
        print(f"❌ Erro: {str(e)}")


def start_scheduler():
    """Inicia o agendador diário às 12h (horário de SP)"""
    scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(
        check_and_update_subscriptions,
        trigger=CronTrigger(hour=12, minute=0),
        name="daily_vip_check"
    )
    scheduler.start()
    print("⏰ Agendador de verificações VIP iniciado!")


if __name__ == "__main__":
    # Para testes locais
    asyncio.run(check_and_update_subscriptions())
