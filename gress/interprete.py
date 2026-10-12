import re
import datetime
from dateparser.search import search_dates

# Palabras con las que empiezas una orden
DISPARADORES = re.compile(
    r"^(apunta(me)?|anota(me)?|recu[eé]rdame)\s+(que\s+)?", re.IGNORECASE
)
# Detecta si dijiste una hora concreta
HORA = re.compile(r"\d{1,2}:\d{2}|\ba las \d{1,2}\b|\b\d{1,2}\s*h\b", re.IGNORECASE)
# "recuérdame en 2 horas...", "recuérdame dentro de 30 minutos que..."
RELATIVO = re.compile(
    r"^recu[eé]rdame\s+(que\s+)?(en|dentro de)\s+(?P<cantidad>\d+)\s*"
    r"(?P<unidad>minutos?|min|horas?|h)\b\s*(que\s+)?(?P<texto>.*)$",
    re.IGNORECASE,
)

AJUSTES = {
    "PREFER_DATES_FROM": "future",
    "TIMEZONE": "Europe/Madrid",
    "RETURN_AS_TIMEZONE_AWARE": False,
}

# Palabras sueltas que dateparser a veces confunde con fechas
FALSOS_POSITIVOS = {"a", "de", "el", "la", "en", "y", "o", "que", "un", "una"}


def capitalizar(texto):
    texto = re.sub(r"\s+", " ", texto).strip(" ,.")
    return texto[:1].upper() + texto[1:]


def interpretar_relativo(texto):
    """Devuelve {'texto', 'cuando'} si es un recordatorio relativo, o None."""
    m = RELATIVO.match(texto.strip())
    if not m:
        return None
    cantidad = int(m.group("cantidad"))
    unidad = m.group("unidad").lower()
    if unidad.startswith("h"):
        delta = datetime.timedelta(hours=cantidad)
    else:
        delta = datetime.timedelta(minutes=cantidad)
    cuando = datetime.datetime.now(datetime.timezone.utc) + delta
    return {"texto": capitalizar(m.group("texto")), "cuando": cuando}


def interpretar(texto):
    """Devuelve {'titulo', 'fecha', 'con_hora'} para el calendario, o None."""
    texto = texto.strip()
    m = DISPARADORES.match(texto)
    if not m:
        return None

    resto = texto[m.end():]
    encontrados = search_dates(resto, languages=["es"], settings=AJUSTES) or []

    # Descarta coincidencias absurdas: palabras de relleno o trocitos muy cortos
    validos = [
        (frase, fecha) for frase, fecha in encontrados
        if frase.strip().lower() not in FALSOS_POSITIVOS and len(frase.strip()) >= 3
    ]

    titulo = resto
    for frase, _ in validos:
        # Borra solo la frase completa, una vez, respetando los límites de palabra
        titulo = re.sub(rf"\b{re.escape(frase)}\b", "", titulo, count=1, flags=re.IGNORECASE)
    titulo = re.sub(r"^\s*(tengo que|hay que|que)\s+", "", titulo.strip(), flags=re.IGNORECASE)
    titulo = capitalizar(titulo)

    if not validos:
        return {"titulo": titulo, "fecha": None, "con_hora": False}

    frase_fecha, fecha = validos[0]
    return {"titulo": titulo, "fecha": fecha, "con_hora": bool(HORA.search(frase_fecha))}


if __name__ == "__main__":
    pruebas = [
        "apunta que mañana tengo que entregar un paquete",
        "recuérdame el viernes a las 17:00 llamar al dentista",
        "apunta que mañana tengo que poner las cosas de vinted a la venta",
        "recuérdame en 2 horas sacar la ropa de la lavadora",
        "recuérdame dentro de 30 minutos que tengo que llamar a casa",
        "hola qué tal",
    ]
    for p in pruebas:
        print(p)
        print("   relativo:", interpretar_relativo(p))
        print("   calendario:", interpretar(p))