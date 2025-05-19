import asyncio
from services.firebase_service import FirebaseService


async def main():
    service = FirebaseService()
    deactivated_users = await service.check_and_update_vip_status()
    print(f"Usuários desativados: {deactivated_users}")

if __name__ == "__main__":
    asyncio.run(main())
