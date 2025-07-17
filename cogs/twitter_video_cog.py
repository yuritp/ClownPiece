import discord
from discord.ext import commands
import re
import os
import logging

from utils.downloader import download_video

log = logging.getLogger(__name__)

class TwitterVideoCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Detecta enlaces de Twitter/X y procesa el video si existe."""
        if message.author.bot:
            return

        match = re.search(r'https?://(twitter|x)\.com/\w+/status/\d+', message.content)
        if match:
            url = match.group(0)
            log.info(f"Enlace de X/Twitter detectado en mensaje de {message.author}: {url}")
            await self.process_twitter_link(url, message.channel)

    async def process_twitter_link(self, url: str, channel: discord.TextChannel):
        """Descarga y envía el video de un enlace de Twitter/X."""
        # El bot envía su propio mensaje de estado
        processing_msg = await channel.send(f"📎 Enlace detectado. Procesando vídeo...")

        video_path = None
        try:
            video_path = download_video(url)

            if video_path and os.path.exists(video_path):
                log.info(f"Vídeo de {url} descargado en '{video_path}'. Enviando a Discord.")
                await channel.send(file=discord.File(video_path))
                await processing_msg.delete()
            elif video_path is None:
                log.warning(f"No se encontró vídeo en el enlace: {url}")
                await processing_msg.edit(content="🤔 No se encontró un vídeo en el enlace.")
        except Exception as e:
            log.error(f"Error procesando el enlace de Twitter {url}", exc_info=e)
            await processing_msg.edit(content=f"🔥 Error durante el proceso: {e}")
        finally:
            if video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                    log.info(f"🧹 Archivo local '{video_path}' eliminado.")
                except OSError as e:
                    log.error(f"🔥 Error al eliminar el archivo local '{video_path}'", exc_info=e)

def setup(bot):
    bot.add_cog(TwitterVideoCog(bot))
