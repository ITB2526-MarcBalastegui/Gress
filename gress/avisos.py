import asyncio
import datetime
import logging
from telegram.ext import ContextTypes

from gress.config import CHAT_ID
from gress.tiempo import tiempo_barcelona
from gress.calendario import eventos_de_hoy, eventos_entre, MADRID

log = logging.getLogger("gress")

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

# Eventos de los que ya ha avisado, para no repetir.
# Se vacía al reiniciar el bot (más adelante lo guardaremos en SQLite).
AVISADOS = set()


def formatear_evento(e):
    if "dateTime" in e["start"]:
        inicio = datetime.datetime.fromisoformat(e["start"]["dateTime"]).astimezone(MADRID)
        hora = inicio.strftime("%H:%M")
    else:
        hora = "Todo el día"
    return f"• {hora}  {e.get('summary', '(sin título)')}"


def texto_resumen():
    hoy = datetime.datetime.now(MADRID)
    partes = [
        f"Buenos días, Marc. Hoy es {DIAS[hoy.weekday()]} {hoy.strftime('%d/%m')}.",
        "",
        tiempo_barcelona(),
        "",
    ]
    eventos = eventos_de_hoy()
    if eventos:
        partes.append("Hoy tienes:")
        partes += [formatear_evento(e) for e in eventos]
    else:
        partes.append("No tienes nada en el calendario hoy.")
    return "\n".join(partes)


async def resumen_manana(context: ContextTypes.DEFAULT_TYPE):
    try:
        texto = await asyncio.to_thread(texto_resumen)
    except Exception:
        log.exception("Error preparando el resumen de la mañana")
        texto = "Buenos días. No he podido preparar el resumen, revisa los logs."
    await context.bot.send_message(chat_id=CHAT_ID, text=texto)


async def comprobar_proximos(context: ContextTypes.DEFAULT_TYPE):
    ahora = datetime.datetime.now(MADRID)
    try:
        eventos = await asyncio.to_thread(
            eventos_entre, ahora, ahora + datetime.timedelta(minutes=60)
        )
    except Exception:
        log.exception("Error consultando el calendario")
        return

    for e in eventos:
        # Ignora eventos de todo el día y los ya avisados
        if "dateTime" not in e["start"] or e["id"] in AVISADOS:
            continue
        inicio = datetime.datetime.fromisoformat(e["start"]["dateTime"])
        if inicio < ahora:
            continue  # Ya ha empezado
        minutos = int((inicio - ahora).total_seconds() // 60)
        AVISADOS.add(e["id"])
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"En {minutos} min: {e.get('summary', '(sin título)')} "
                 f"({inicio.astimezone(MADRID).strftime('%H:%M')})",
        )