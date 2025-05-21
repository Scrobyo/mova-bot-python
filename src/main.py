import asyncio
from bot.bot import BotRunner
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def main():
    logger.info("Iniciando o bot...")
    runner = BotRunner()
    await runner.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot encerrado pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        raise
