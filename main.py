# main.py
import discord
from flask import Flask
import threading
from config import Config
from web.routes import setup_routes
import os
import logging
from utils.logger_setup import setup_logging  # <-- IMPORTAMOS LA CONFIGURACIÓN

# --- Configuración del Logging y el Bot ---
setup_logging()  # <-- INICIALIZAMOS LOS LOGS AL PRINCIPIO DE TODO
log = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.members = True

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    log.info(f"✅ {bot.user} se ha conectado a Discord!")
    log.info(f"🌍 Panel de control web disponible en http://127.0.0.1:5000")


# --- Configuración del Servidor Web Flask ---
app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
app.secret_key = Config.FLASK_SECRET_KEY
web_routes = setup_routes(bot)
app.register_blueprint(web_routes)


# --- Carga de Cogs y Ejecución ---
def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                bot.load_extension(f'cogs.{filename[:-3]}')
                log.info(f"🔩 Cog '{filename[:-3]}' cargado.")
            except Exception as e:
                log.error(f"🔥 Error al cargar el cog '{filename[:-3]}'", exc_info=e)


if __name__ == "__main__":
    if not Config.TOKEN:
        log.critical("🚨 ERROR: El token de Discord no está configurado en el archivo .env")
    else:
        load_cogs()

        flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False))
        flask_thread.daemon = True
        flask_thread.start()

        bot.run(Config.TOKEN)