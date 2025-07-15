from flask import Blueprint, render_template, request, flash, redirect, url_for
import asyncio
import re
import discord
from utils.downloader import download_video  # Asegúrate de que esta importación sea correcta
import os

web_blueprint = Blueprint('web', __name__, static_folder='static', template_folder='templates')


def setup_routes(bot):
    @web_blueprint.route('/')
    def index():
        last_text_channel = request.args.get('last_text_channel')
        last_voice_channel = request.args.get('last_voice_channel')
        guilds_data = []
        if bot.is_ready():
            for guild in bot.guilds:
                guilds_data.append({
                    "guild_name": guild.name,
                    "channels": sorted(guild.text_channels, key=lambda c: c.name),
                    "voice_channels": sorted(guild.voice_channels, key=lambda c: c.name)
                })
        return render_template('index.html', guilds_data=guilds_data, last_text_channel=last_text_channel,
                               last_voice_channel=last_voice_channel)

    @web_blueprint.route('/enviar', methods=['POST'])
    def enviar():
        submit_type = request.form.get('submit_type', 'simple')
        channel_id = request.form['channel_id']

        if submit_type == 'embed':
            try:
                title = request.form.get('embed_title', '')
                description = request.form.get('embed_description', '')
                color_hex = request.form.get('embed_color', '#000000').lstrip('#')
                color = discord.Color(int(color_hex, 16))
                embed = discord.Embed(title=title, description=description, color=color)
                future = asyncio.run_coroutine_threadsafe(send_embed_to_discord(bot, channel_id, embed), bot.loop)
                future.result()
                flash("✅ Embed enviado con éxito.", "success")
            except Exception as e:
                flash(f"🔥 Error al enviar el embed: {e}", "error")
        else:
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
                flash(f"🔥 Error al ejecutar la tarea: {e}", "error")

        return redirect(url_for('web.index', last_text_channel=channel_id))

    @web_blueprint.route('/control-voz', methods=['POST'])
    def control_voz():
        channel_id = request.form.get('channel_id')
        action = request.form.get('action')

        if not channel_id:
            flash("❌ Debes seleccionar un canal de voz.", "error")
            return redirect(url_for('web.index'))

        if action == 'join':
            future = asyncio.run_coroutine_threadsafe(join_voice_channel(bot, channel_id), bot.loop)
        elif action == 'leave':
            future = asyncio.run_coroutine_threadsafe(leave_voice_channel(bot), bot.loop)
        else:
            flash("Acción de voz no reconocida.", "error")
            return redirect(url_for('web.index'))

        try:
            msg, status = future.result()
            flash(msg, status)
        except Exception as e:
            flash(f"🔥 Error en la acción de voz: {e}", "error")
        return redirect(url_for('web.index', last_voice_channel=channel_id))

    return web_blueprint


# --- Funciones Asíncronas de Ayuda ---
async def join_voice_channel(bot, channel_id):
    channel = bot.get_channel(int(channel_id))
    if not isinstance(channel, discord.VoiceChannel):
        return ("Canal de voz no válido.", "error")
    if bot.voice_clients:
        await bot.voice_clients[0].move_to(channel)
    else:
        await channel.connect()
    return (f"✅ Conectado a {channel.name}", "success")


async def leave_voice_channel(bot):
    if bot.voice_clients:
        await bot.voice_clients[0].disconnect()
        return ("👋 Desconectado del canal de voz.", "success")
    else:
        return ("🤷 No estoy en ningún canal de voz.", "error")


async def send_to_discord_channel(bot, channel_id, message, file_storage):
    try:
        channel = await bot.fetch_channel(int(channel_id))
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
        print(f"🔥 Error enviando desde la web: {e}")
        return f"🔥 No se pudo enviar el mensaje: {e}", "error"


async def send_embed_to_discord(bot, channel_id, embed):
    channel = await bot.fetch_channel(int(channel_id))
    await channel.send(embed=embed)