import asyncio
from gress.interprete import interpretar
from gress.calendario import crear_evento, proximos_eventos
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


DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


async def texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    r = interpretar(update.message.text)

    if r is None:
        await update.message.reply_text(
            "No te he entendido. Empieza con 'apunta que...' o 'recuérdame...'."
        )
        return
    if not r["titulo"]:
        await update.message.reply_text("¿Qué quieres que apunte?")
        return
    if r["fecha"] is None:
        await update.message.reply_text(
            f"Vale, '{r['titulo']}', pero ¿para cuándo? Dímelo en la frase, por ejemplo 'apunta que el lunes...'."
        )
        return

    try:
        # La API de Google es bloqueante; la ejecutamos aparte para no congelar el bot
        await asyncio.to_thread(crear_evento, r["titulo"], r["fecha"], r["con_hora"])
    except Exception:
        log.exception("Error creando evento")
        await update.message.reply_text("No he podido crear el evento. Mira los logs.")
        return

    f = r["fecha"]
    cuando = f"{DIAS[f.weekday()]} {f.strftime('%d/%m/%Y')}"
    if r["con_hora"]:
        cuando += f" a las {f.strftime('%H:%M')}"
    await update.message.reply_text(f"Apuntado: {r['titulo']}, {cuando}.")


async def agenda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    eventos = await asyncio.to_thread(proximos_eventos, 5)
    if not eventos:
        await update.message.reply_text("No tienes eventos próximos.")
        return
    lineas = []
    for e in eventos:
        inicio = e["start"].get("dateTime", e["start"].get("date"))
        lineas.append(f"• {inicio[:16].replace('T', ' ')}  {e.get('summary', '(sin título)')}")
    await update.message.reply_text("Próximos eventos:\n" + "\n".join(lineas))

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
    app.add_handler(CommandHandler("agenda", agenda, filters=SOLO_MARC))
    log.info("Gress arrancado, esperando mensajes...")
    app.run_polling()
    


if __name__ == "__main__":
    main()