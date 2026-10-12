import asyncio
import datetime
import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters,
)

from gress.config import TELEGRAM_TOKEN, CHAT_ID
from gress.tiempo import tiempo_barcelona
from gress.interprete import interpretar
from gress.calendario import crear_evento, proximos_eventos, MADRID
from gress.avisos import resumen_manana, comprobar_proximos, texto_resumen

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
# httpx registra las URLs completas, que incluyen el token. Lo silenciamos.
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("gress")

# Solo acepta mensajes de tu chat
SOLO_MARC = filters.Chat(chat_id=CHAT_ID)

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Gress en línea.\n"
        "/ping - comprobar que estoy vivo\n"
        "/tiempo - previsión de hoy\n"
        "/agenda - próximos eventos\n"
        "/resumen - resumen del día\n\n"
        "Para apuntar algo: 'apunta que mañana...' o 'recuérdame el viernes a las 17:00...'"
    )


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong")


async def tiempo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = await asyncio.to_thread(tiempo_barcelona)
    await update.message.reply_text(texto)


async def agenda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        eventos = await asyncio.to_thread(proximos_eventos, 5)
    except Exception:
        log.exception("Error leyendo la agenda")
        await update.message.reply_text("No he podido leer el calendario. Mira los logs.")
        return

    if not eventos:
        await update.message.reply_text("No tienes eventos próximos.")
        return

    lineas = []
    for e in eventos:
        inicio = e["start"].get("dateTime", e["start"].get("date"))
        lineas.append(f"• {inicio[:16].replace('T', ' ')}  {e.get('summary', '(sin título)')}")
    await update.message.reply_text("Próximos eventos:\n" + "\n".join(lineas))


async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        texto = await asyncio.to_thread(texto_resumen)
    except Exception:
        log.exception("Error preparando el resumen")
        texto = "No he podido preparar el resumen. Mira los logs."
    await update.message.reply_text(texto)


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
            f"Vale, '{r['titulo']}', pero ¿para cuándo? "
            "Dímelo en la frase, por ejemplo 'apunta que el lunes...'."
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


async def intruso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = update.effective_user
    log.warning("Mensaje ignorado de %s (id %s)", usuario.username, usuario.id)


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start, filters=SOLO_MARC))
    app.add_handler(CommandHandler("ping", ping, filters=SOLO_MARC))
    app.add_handler(CommandHandler("tiempo", tiempo, filters=SOLO_MARC))
    app.add_handler(CommandHandler("agenda", agenda, filters=SOLO_MARC))
    app.add_handler(CommandHandler("resumen", resumen, filters=SOLO_MARC))

    # Mensajes de texto
    app.add_handler(MessageHandler(SOLO_MARC & filters.TEXT & ~filters.COMMAND, texto))
    app.add_handler(MessageHandler(~SOLO_MARC, intruso))

    # Tareas programadas
    jq = app.job_queue
    jq.run_daily(resumen_manana, time=datetime.time(7, 30, tzinfo=MADRID), name="resumen_manana")
    jq.run_repeating(comprobar_proximos, interval=300, first=10, name="avisos_eventos")

    log.info("Gress arrancado, esperando mensajes...")
    app.run_polling()


if __name__ == "__main__":
    main()