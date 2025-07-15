# web/routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
import asyncio
import re
from utils.downloader import download_video
import os
import discord

web_blueprint = Blueprint('web', __name__)


def setup_routes(bot):
    @web_blueprint.route('/')
    def index():
        channels_by_guild = []
        if bot.is_ready():
            for guild in bot.guilds:
                text_channels = sorted(guild.text_channels, key=lambda c: c.name)
                if text_channels:
                    channels_by_guild.append({"guild_name": guild.name, "channels": text_channels})
        return render_template('index.html', guilds_data=channels_by_guild)

    @web_blueprint.route('/enviar-discord', methods=['POST'])
    def enviar_discord():
        channel_id = int(request.form['channel_id'])
        message_content = request.form.get('message', '')
        file = request.files.get('file')

        if not message_content and not file:
            flash("❌ Debes incluir un mensaje o un archivo.", "error")
            return redirect(url_for('web.index'))

        future = asyncio.run_coroutine_threadsafe(
            send_to_discord_channel(bot, channel_id, message_content, file),
            bot.loop
        )

        try:
            result_message, status = future.result()
            flash(result_message, status)
        except Exception as e:
            flash(f"🔥 Error al ejecutar la tarea: {e}", "error")

        return redirect(url_for('web.index'))

    return web_blueprint


async def send_to_discord_channel(bot, channel_id, message, file_storage):
    try:
        channel = await bot.fetch_channel(channel_id)

        discord_file = None
        if file_storage and file_storage.filename != '':
            discord_file = discord.File(file_storage.stream, filename=file_storage.filename)

        sent_message = await channel.send(content=message, file=discord_file)

        match = re.search(r'https?://(twitter|x)\.com/\w+/status/\d+', message)
        if match:
            events_cog = bot.get_cog("EventsCog")
            if events_cog:
                bot.loop.create_task(
                    events_cog.process_twitter_link(match.group(0), channel, sent_message)
                )

        return "✅ Mensaje enviado con éxito.", "success"
    except Exception as e:
        print(f"🔥 Error enviando desde la web: {e}")
        return f"🔥 No se pudo enviar el mensaje: {e}", "error"