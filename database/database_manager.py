# database/database_manager.py
import sqlite3
import logging
from datetime import datetime

log = logging.getLogger(__name__)

DB_FILE = "clownpiece_data.db"


def init_db():
    """
    Inicializa la base de datos y crea las tablas si no existen.
    Se debe llamar una sola vez cuando el bot arranca.
    """
    try:
        con = sqlite3.connect(DB_FILE)
        cur = con.cursor()

        # --- Tabla para los Logs de Auditoría ---
        # Guardará todos los eventos importantes del servidor.
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS audit_logs
                    (
                        id
                        INTEGER
                        PRIMARY
                        KEY
                        AUTOINCREMENT,
                        timestamp
                        TEXT
                        NOT
                        NULL,
                        event_type
                        TEXT
                        NOT
                        NULL,
                        author_id
                        INTEGER,
                        channel_id
                        INTEGER,
                        message
                        TEXT,
                        details
                        TEXT
                    )
                    """)

        # Aquí podrías añadir más tablas en el futuro (ej. para economía, XP, etc.)
        # cur.execute("CREATE TABLE IF NOT EXISTS economy ( ... )")

        con.commit()
        con.close()
        log.info(f"Base de datos '{DB_FILE}' inicializada correctamente.")
    except Exception as e:
        log.critical("¡¡¡ NO SE PUDO INICIALIZAR LA BASE DE DATOS !!!", exc_info=e)


def add_log(event_type: str, author_id: int = None, channel_id: int = None, message: str = None, details: str = None):
    """
    Añade un nuevo registro a la tabla de logs de auditoría.
    """
    try:
        con = sqlite3.connect(DB_FILE)
        cur = con.cursor()

        timestamp = datetime.utcnow().isoformat()

        cur.execute(
            "INSERT INTO audit_logs (timestamp, event_type, author_id, channel_id, message, details) VALUES (?, ?, ?, ?, ?, ?)",
            (timestamp, event_type, author_id, channel_id, message, details)
        )

        con.commit()
        con.close()
    except Exception as e:
        log.error(f"Error al añadir un log a la base de datos.", exc_info=e)


def get_all_logs():
    """
    Recupera todos los registros de la tabla de logs de auditoría.
    Devuelve una lista de diccionarios para fácil manejo.
    """
    try:
        con = sqlite3.connect(DB_FILE)
        # Permite acceder a los resultados por nombre de columna
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC")

        # Convierte los resultados en una lista de diccionarios
        logs = [dict(row) for row in cur.fetchall()]

        con.close()
        return logs
    except Exception as e:
        log.error("Error al recuperar los logs de la base de datos.", exc_info=e)
        return []