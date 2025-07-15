# config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Clase para centralizar la configuración del bot y la aplicación web."""
    # Token de Discord
    TOKEN = os.getenv("DISCORD_TOKEN")

    # Configuración de la aplicación Flask
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", os.urandom(24))

    # Ruta para guardar las descargas
    DOWNLOADS_PATH = "downloads"

    # ID del canal donde se registrarán los eventos (logs de auditoría)
    AUDIT_LOG_CHANNEL_ID = 1394673936385576991
