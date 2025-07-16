import sqlite3
import logging
from datetime import datetime, timezone

log = logging.getLogger(__name__)

DB_FILE = "clownpiece_data.db"

class DatabaseConnection:
    """Un gestor de contexto para manejar las conexiones a la base de datos de forma segura."""
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None

    def __enter__(self):
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row
            return self.conn.cursor()
        except sqlite3.Error as e:
            log.error(f"Error al conectar con la base de datos: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.commit()
            self.conn.close()

def init_db():
    """Inicializa la base de datos y crea las tablas si no existen."""
    try:
        with DatabaseConnection(DB_FILE) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    author_id INTEGER,
                    channel_id INTEGER,
                    message TEXT,
                    details TEXT
                )
            """)
        log.info(f"Base de datos '{DB_FILE}' inicializada correctamente.")
    except Exception as e:
        log.critical("¡¡¡ NO SE PUDO INICIALIZAR LA BASE DE DATOS !!!", exc_info=e)

def add_log(event_type: str, author_id: int = None, channel_id: int = None, message: str = None, details: str = None):
    """Añade un nuevo registro a la tabla de logs de auditoría."""
    try:
        with DatabaseConnection(DB_FILE) as cur:
            timestamp = datetime.now(timezone.utc).isoformat()
            cur.execute(
                "INSERT INTO audit_logs (timestamp, event_type, author_id, channel_id, message, details) VALUES (?, ?, ?, ?, ?, ?)",
                (timestamp, event_type, author_id, channel_id, message, details)
            )
    except Exception as e:
        log.error("Error al añadir un log a la base de datos.", exc_info=e)

def get_all_logs() -> list[dict]:
    """Recupera todos los registros de la tabla de logs de auditoría."""
    try:
        with DatabaseConnection(DB_FILE) as cur:
            cur.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC")
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        log.error("Error al recuperar los logs de la base de datos.", exc_info=e)
        return []

# Inicializar la base de datos al cargar el módulo
init_db()