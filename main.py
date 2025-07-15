import discord
from flask import Flask
import threading
import os
import logging

# --- IMPORTACIONES LOCALES ---
from config import Config
from web.routes import setup_routes
from utils.logger_setup import setup_logging
from database.database_manager import init_db

# --- CONFIGURACIÓN INICIAL ---
# 1. Configura el sistema de logging para todo el proyecto
setup_logging()
# 2. Inicializa la base de datos y crea las tablas si no existen
init_db()
# 3. Obtiene un logger para este módulo
log = logging.getLogger(__name__)

# --- CONFIGURACIÓN DEL BOT DE DISCORD ---
# Definimos los "Intents" (permisos) que nuestro bot necesita
intents = discord.Intents.default()
intents.guilds = True  # Para información del servidor (canales, etc.)
intents.message_content = True  # Para leer el contenido de los mensajes
intents.members = True  # Para eventos de miembros (unirse/salir)

# Creamos la instancia del bot
bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    """Se ejecuta cuando el bot se conecta exitosamente a Discord."""
    log.info(f"✅ {bot.user} se ha conectado a Discord!")
    log.info(f"🌍 Panel de control web disponible en http://127.0.0.1:5000")


# --- CONFIGURACIÓN DEL SERVIDOR WEB FLASK ---
# Le decimos a Flask dónde encontrar las plantillas y archivos estáticos
app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
app.secret_key = Config.FLASK_SECRET_KEY

# Registramos las rutas definidas en web/routes.py
web_routes = setup_routes(bot)
app.register_blueprint(web_routes)


# --- CARGA DE COGS Y EJECUCIÓN ---
def load_cogs():
    """Busca y carga todas las extensiones (Cogs) en la carpeta 'cogs'."""
    log.info("Cargando todos los cogs...")
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                bot.load_extension(f'cogs.{filename[:-3]}')
                log.info(f"🔩 Cog '{filename[:-3]}' cargado.")
            except Exception as e:
                # Usamos exc_info=e para un traceback completo en la consola
                log.error(f"🔥 Error al cargar el cog '{filename[:-3]}'", exc_info=e)


if __name__ == "__main__":
    if not Config.TOKEN:
        log.critical("🚨 ¡ERROR CRÍTICO! El token de Discord no está configurado en el archivo .env")
    else:
        # Cargamos las extensiones antes de ejecutar el bot
        load_cogs()

        # Iniciamos el servidor Flask en un hilo separado para que no bloquee al bot
        flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False))
        flask_thread.daemon = True
        flask_thread.start()

        # Iniciamos el bot de Discord
        bot.run(Config.TOKEN)