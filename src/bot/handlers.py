from telegram.ext import CommandHandler


async def start(update, context):
    await update.message.reply_text("Olá! Eu sou o MovaBot. Digite /start para começar.")


def setup_handlers(application):
    application.add_handler(CommandHandler("start", start))
