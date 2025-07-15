# main.py
import discord
from flask import Flask
import threading
from config import Config
from web.routes import setup_routes
import os

# --- Configuración del Bot de Discord ---
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.members = True  # <-- INTENT NECESARIO PARA on_member_join y on_member_remove

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    print("=" * 30)
    print(f'✅ {bot.user} se ha conectado a Discord!')
    print(f"🌍 Panel de control web disponible en http://127.0.0.1:5000")
    print("=" * 30)


# --- Configuración del Servidor Web Flask ---
app = Flask(__name__)
app.secret_key = Config.FLASK_SECRET_KEY
# Registramos el Blueprint de las rutas web
web_routes = setup_routes(bot)
app.register_blueprint(web_routes)


# --- Carga de Cogs y Ejecución ---
def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"🔩 Cog '{filename[:-3]}' cargado.")
            except Exception as e:
                print(f"🔥 Error al cargar el cog '{filename[:-3]}': {e}")


if __name__ == "__main__":
    if not Config.TOKEN:
        print("🚨 ERROR: El token de Discord no está configurado en el archivo .env")
    else:
        load_cogs()

        # Iniciar Flask en un hilo separado
        flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False))
        flask_thread.daemon = True
        flask_thread.start()

        # Iniciar el bot de Discord
        bot.run(Config.TOKEN)