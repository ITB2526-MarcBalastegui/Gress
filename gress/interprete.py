import re
from dateparser.search import search_dates

# Palabras con las que empiezas una orden
DISPARADORES = re.compile(
    r"^(apunta(me)?|anota(me)?|recu[eé]rdame)\s+(que\s+)?", re.IGNORECASE
)
# Detecta si dijiste una hora concreta
HORA = re.compile(r"\d{1,2}:\d{2}|\ba las \d{1,2}\b|\b\d{1,2}\s*h\b", re.IGNORECASE)

AJUSTES = {
    "PREFER_DATES_FROM": "future",
    "TIMEZONE": "Europe/Madrid",
    "RETURN_AS_TIMEZONE_AWARE": False,
}


# Palabras sueltas que dateparser a veces confunde con fechas
FALSOS_POSITIVOS = {"a", "de", "el", "la", "en", "y", "o", "que", "un", "una"}


def interpretar(texto):
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
    titulo = re.sub(r"\s+", " ", titulo).strip(" ,.")
    titulo = titulo[:1].upper() + titulo[1:]

    if not validos:
        return {"titulo": titulo, "fecha": None, "con_hora": False}

    frase_fecha, fecha = validos[0]
    return {"titulo": titulo, "fecha": fecha, "con_hora": bool(HORA.search(frase_fecha))}

if __name__ == "__main__":
    pruebas = [
        "apunta que mañana tengo que entregar un paquete",
        "recuérdame el viernes a las 17:00 llamar al dentista",
        "apunta comprar pan",
        "hola qué tal",
        "apunta que mañana tengo que poner las cosas de vinted a la venta",
        "apunta que el jueves voy a casa de mi abuela",
    ]
    for p in pruebas:
        print(p, "->", interpretar(p))