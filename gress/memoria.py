"""
Memoria persistente de Gress con SQLite.
Todas las fechas se guardan en UTC y en formato ISO, para que se puedan
comparar y ordenar sin líos con el cambio de hora.
"""
import sqlite3
import datetime
from contextlib import closing

RUTA = "gress.db"


def conectar():
    con = sqlite3.connect(RUTA)
    con.row_factory = sqlite3.Row  # Permite acceder a las columnas por nombre
    return con


def ahora_utc():
    return datetime.datetime.now(datetime.timezone.utc)


def iniciar():
    with closing(conectar()) as con, con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS avisados (
                evento_id TEXT PRIMARY KEY,
                avisado_en TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS recordatorios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                texto TEXT NOT NULL,
                cuando TEXT NOT NULL,
                enviado INTEGER NOT NULL DEFAULT 0,
                creado TEXT NOT NULL
            )
        """)


# ---------- Avisos de eventos del calendario ----------

def ya_avisado(evento_id):
    with closing(conectar()) as con:
        fila = con.execute("SELECT 1 FROM avisados WHERE evento_id = ?", (evento_id,)).fetchone()
        return fila is not None


def marcar_avisado(evento_id):
    with closing(conectar()) as con, con:
        con.execute(
            "INSERT OR IGNORE INTO avisados (evento_id, avisado_en) VALUES (?, ?)",
            (evento_id, ahora_utc().isoformat()),
        )


def limpiar_avisados(dias=7):
    limite = (ahora_utc() - datetime.timedelta(days=dias)).isoformat()
    with closing(conectar()) as con, con:
        con.execute("DELETE FROM avisados WHERE avisado_en < ?", (limite,))


# ---------- Recordatorios propios ----------

def crear_recordatorio(texto, cuando):
    with closing(conectar()) as con, con:
        cur = con.execute(
            "INSERT INTO recordatorios (texto, cuando, creado) VALUES (?, ?, ?)",
            (texto, cuando.astimezone(datetime.timezone.utc).isoformat(), ahora_utc().isoformat()),
        )
        return cur.lastrowid


def recordatorios_vencidos():
    with closing(conectar()) as con:
        return con.execute(
            "SELECT * FROM recordatorios WHERE enviado = 0 AND cuando <= ? ORDER BY cuando",
            (ahora_utc().isoformat(),),
        ).fetchall()


def recordatorios_pendientes():
    with closing(conectar()) as con:
        return con.execute(
            "SELECT * FROM recordatorios WHERE enviado = 0 ORDER BY cuando"
        ).fetchall()


def marcar_enviado(rec_id):
    with closing(conectar()) as con, con:
        con.execute("UPDATE recordatorios SET enviado = 1 WHERE id = ?", (rec_id,))


def borrar_recordatorio(rec_id):
    with closing(conectar()) as con, con:
        cur = con.execute("DELETE FROM recordatorios WHERE id = ? AND enviado = 0", (rec_id,))
        return cur.rowcount > 0