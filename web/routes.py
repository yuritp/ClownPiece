from flask import Blueprint, render_template, request, flash, redirect, url_for
import asyncio
import re
import discord
from utils.downloader import download_video
import os
import logging

# Obtenemos un logger específico para este módulo
log = logging.getLogger(__name__)

# Creamos el Blueprint para organizar las rutas
web_blueprint = Blueprint('web', __name__, static_folder='static', template_folder='templates')


def setup_routes(bot):
    """
    Configura todas las rutas para la aplicación web y las asocia con el bot.
    """

    @web_blueprint.route('/')
    def index():
        """
        Renderiza la página principal del panel de control.
        """
        last_text_channel = request.args.get('last_text_channel')
        last_voice_channel = request.args.get('last_voice_channel')

        guilds_data = []
        if bot.is_ready():
            for guild in bot.guilds:
                guild_info = {
                    "guild_name": guild.name,
                    "channels": sorted(guild.text_channels, key=lambda c: c.name),
                    "voice_channels": sorted(guild.voice_channels, key=lambda c: c.name)
                }
                guilds_data.append(guild_info)

        return render_template(
            'index.html',
            guilds_data=guilds_data,
            last_text_channel=last_text_channel,
            last_voice_channel=last_voice_channel
        )

    @web_blueprint.route('/enviar', methods=['POST'])
    def enviar():
        """
        Maneja el envío de mensajes (simples o embeds) desde la web.
        """
        submit_type = request.form.get('submit_type', 'simple')
        channel_id = request.form['channel_id']
        log.info(f"Petición web /enviar recibida. Tipo: {submit_type}, Canal: {channel_id}")

        if submit_type == 'embed':
            try:
                title = request.form.get('embed_title', '')
                description = request.form.get('embed_description', '')
                color_hex = request.form.get('embed_color', '#000000').lstrip('#')
                color = discord.Color(int(color_hex, 16))
                embed = discord.Embed(title=title, description=description, color=color)

                future = asyncio.run_coroutine_threadsafe(send_embed_to_discord(bot, channel_id, embed), bot.loop)
                future.result()  # Espera a que se complete
                flash("✅ Embed enviado con éxito.", "success")
            except Exception as e:
                log.error(f"Error al procesar el envío de embed desde la web.", exc_info=e)
                flash(f"🔥 Error al enviar el embed: {e}", "error")
        else:  # Mensaje simple
            message_content = request.form.get('message', '')
            file = request.files.get('file')
            if not message_content and not file:
                flash("❌ Debes incluir un mensaje o un archivo.", "error")
                return redirect(url_for('web.index', last_text_channel=channel_id))

            future = asyncio.run_coroutine_threadsafe(send_to_discord_channel(bot, channel_id, message_content, file),
                                                      bot.loop)
            try:
                result_message, status = future.result()
                flash(result_message, status)
            except Exception as e:
                log.error(f"Error en la tarea de envío de mensaje desde la web.", exc_info=e)
                flash(f"🔥 Error al ejecutar la tarea: {e}", "error")

        return redirect(url_for('web.index', last_text_channel=channel_id))

    @web_blueprint.route('/control-voz', methods=['POST'])
    def control_voz():
        """
        Maneja las acciones de voz (unirse/salir) desde la web.
        """
        channel_id = request.form.get('channel_id')
        action = request.form.get('action')
        log.info(f"Petición web /control-voz recibida. Acción: {action}, Canal: {channel_id}")

        if not channel_id:
            flash("❌ Debes seleccionar un canal de voz.", "error")
            return redirect(url_for('web.index'))

        if action == 'join':
            future = asyncio.run_coroutine_threadsafe(join_voice_channel(bot, channel_id), bot.loop)
        elif action == 'leave':
            future = asyncio.run_coroutine_threadsafe(leave_voice_channel(bot), bot.loop)
        else:
            log.warning(f"Acción de voz no reconocida: {action}")
            flash("Acción de voz no reconocida.", "error")
            return redirect(url_for('web.index'))

        try:
            msg, status = future.result()
            flash(msg, status)
        except Exception as e:
            log.error(f"Error en la acción de voz desde la web.", exc_info=e)
            flash(f"🔥 Error en la acción de voz: {e}", "error")

        return redirect(url_for('web.index', last_voice_channel=channel_id))

    return web_blueprint


# --- Funciones Asíncronas de Ayuda (se ejecutan en el hilo del bot) ---

async def join_voice_channel(bot, channel_id):
    channel = bot.get_channel(int(channel_id))
    if not isinstance(channel, discord.VoiceChannel):
        return ("Canal de voz no válido.", "error")
    if bot.voice_clients:
        log.info(f"Moviendo el bot al canal de voz '{channel.name}'.")
        await bot.voice_clients[0].move_to(channel)
    else:
        log.info(f"Conectando el bot al canal de voz '{channel.name}'.")
        await channel.connect()
    return (f"✅ Conectado a {channel.name}", "success")


async def leave_voice_channel(bot):
    if bot.voice_clients:
        log.info(f"Desconectando del canal de voz '{bot.voice_clients[0].channel.name}'.")
        await bot.voice_clients[0].disconnect()
        return ("👋 Desconectado del canal de voz.", "success")
    else:
        return ("🤷 No estoy en ningún canal de voz.", "error")


async def send_to_discord_channel(bot, channel_id, message, file_storage):
    try:
        channel = await bot.fetch_channel(int(channel_id))
        log.info(f"Enviando mensaje desde la web al canal '{channel.name}'.")

        discord_file = None
        if file_storage and file_storage.filename != '':
            discord_file = discord.File(file_storage.stream, filename=file_storage.filename)

        sent_message = await channel.send(content=message, file=discord_file)

        match = re.search(r'https?://(twitter|x)\.com/\w+/status/\d+', message)
        if match:
            events_cog = bot.get_cog("EventsCog")
            if events_cog:
                bot.loop.create_task(events_cog.process_twitter_link(match.group(0), channel, sent_message))

        return "✅ Mensaje enviado con éxito.", "success"
    except Exception as e:
        log.error(f"No se pudo enviar el mensaje web al canal {channel_id}", exc_info=e)
        return f"🔥 No se pudo enviar el mensaje: {e}", "error"


async def send_embed_to_discord(bot, channel_id, embed):
    try:
        channel = await bot.fetch_channel(int(channel_id))
        log.info(f"Enviando embed desde la web al canal '{channel.name}'.")
        await channel.send(embed=embed)
    except Exception as e:
        log.error(f"No se pudo enviar el embed web al canal {channel_id}", exc_info=e)
        raise e