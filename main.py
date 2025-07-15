import discord
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, flash, redirect, url_for
import threading
import asyncio
import re  # <-- Importamos re para buscar links

# Carga de variables de entorno
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# --- Configuración del Bot de Discord ---
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True  # <-- ¡EL PERMISO CLAVE QUE FALTABA!

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    print("=" * 30)
    print(f'✅ {bot.user} se ha conectado a Discord!')
    print(f"🌍 Panel de control web disponible en http://127.0.0.1:5000")
    print("=" * 30)


# Carga de Cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py') and filename != '__init__.py':
        bot.load_extension(f'cogs.{filename[:-3]}')

# --- Configuración del Servidor Web Flask ---
app = Flask(__name__)
app.secret_key = os.urandom(24)


@app.route('/')
def index():
    channels_by_guild = []
    if bot.is_ready():
        for guild in bot.guilds:
            text_channels = sorted(guild.text_channels, key=lambda c: c.name)
            if text_channels:
                channels_by_guild.append({"guild_name": guild.name, "channels": text_channels})
    return render_template('index.html', guilds_data=channels_by_guild)


@app.route('/enviar-discord', methods=['POST'])
def enviar_discord():
    channel_id = int(request.form['channel_id'])
    message_content = request.form.get('message', '')
    file = request.files.get('file')

    if not message_content and not file:
        flash("❌ Debes incluir un mensaje o un archivo.", "error")
        return redirect(url_for('index'))

    future = asyncio.run_coroutine_threadsafe(
        send_to_discord_channel(channel_id, message_content, file),
        bot.loop
    )

    try:
        result_message, status = future.result()
        flash(result_message, status)
    except Exception as e:
        flash(f"🔥 Error al ejecutar la tarea: {e}", "error")

    return redirect(url_for('index'))


async def send_to_discord_channel(channel_id, message, file_storage):
    try:
        channel = await bot.fetch_channel(channel_id)

        discord_file = None
        if file_storage and file_storage.filename != '':
            discord_file = discord.File(file_storage.stream, filename=file_storage.filename)

        # Enviamos el mensaje o archivo inicial
        sent_message = await channel.send(content=message, file=discord_file)

        # --- LÓGICA AÑADIDA PARA PROCESAR LINKS DESDE LA WEB ---
        # Buscamos un link de Twitter en el texto que acabamos de enviar
        match = re.search(r'https?://(twitter|x)\.com/\w+/status/\d+', message)
        if match:
            # Si se encuentra, obtenemos el Cog de eventos y llamamos a la función de procesado
            events_cog = bot.get_cog("EventsCog")
            if events_cog:
                # Creamos una tarea para que no bloquee la respuesta de la web
                bot.loop.create_task(
                    events_cog._process_twitter_link(match.group(0), channel, sent_message)
                )

        return "✅ Mensaje enviado con éxito.", "success"
    except Exception as e:
        print(f"🔥 Error enviando desde la web: {e}")
        return f"🔥 No se pudo enviar el mensaje: {e}", "error"


# --- Ejecución ---
if __name__ == "__main__":
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False))
    flask_thread.daemon = True
    flask_thread.start()
    bot.run(TOKEN)