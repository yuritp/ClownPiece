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
