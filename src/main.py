import asyncio
from bot.bot import run_bot
from utils.logger import setup_logger

logger = setup_logger("main")

if __name__ == "__main__":
    logger.info("Iniciando o bot...")
    asyncio.run(run_bot())
