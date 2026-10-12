import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters,
)

from gress.config import TELEGRAM_TOKEN, CHAT_ID
from gress.tiempo import tiempo_barcelona

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("gress")
logging.getLogger("httpx").setLevel(logging.WARNING)
# Solo acepta mensajes de tu chat
SOLO_MARC = filters.Chat(chat_id=CHAT_ID)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Gress en línea.\n"
        "/ping - comprobar que estoy vivo\n"
        "/tiempo - previsión de hoy"
    )


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong")


async def tiempo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(tiempo_barcelona())


async def texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # De momento repite. Aquí irá luego lo de "apunta que..."
    await update.message.reply_text(f"Recibido: {update.message.text}")


async def intruso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = update.effective_user
    log.warning("Mensaje ignorado de %s (id %s)", usuario.username, usuario.id)


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start, filters=SOLO_MARC))
    app.add_handler(CommandHandler("ping", ping, filters=SOLO_MARC))
    app.add_handler(CommandHandler("tiempo", tiempo, filters=SOLO_MARC))
    app.add_handler(MessageHandler(SOLO_MARC & filters.TEXT & ~filters.COMMAND, texto))
    app.add_handler(MessageHandler(~SOLO_MARC, intruso))

    log.info("Gress arrancado, esperando mensajes...")
    app.run_polling()


if __name__ == "__main__":
    main()