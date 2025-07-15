# cogs/events_cog.py
import discord
from discord.ext import commands
import re
import os
from utils.downloader import download_video
from config import Config


class EventsCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        match = re.search(r'https?://(twitter|x)\.com/\w+/status/\d+', message.content)
        if match:
            await self.process_twitter_link(match.group(0), message.channel)

    async def process_twitter_link(self, url: str, channel: discord.TextChannel,
                                   original_message: discord.Message = None):
        if original_message:
            processing_msg = original_message
            await processing_msg.edit(content=f"{processing_msg.content}\n\n*📎 Procesando vídeo...*")
        else:
            processing_msg = await channel.send(f"📎 Enlace detectado. Procesando vídeo...")

        video_path = None
        try:
            video_path = download_video(url)

            if video_path and os.path.exists(video_path):
                await channel.send(file=discord.File(video_path))

                if original_message:
                    clean_content = re.sub(r'\n\n\*📎 Procesando vídeo...\*', '', processing_msg.content)
                    await processing_msg.edit(content=clean_content)
                else:
                    await processing_msg.delete()
            elif video_path is None:
                await processing_msg.edit(content="🤔 No se encontró un vídeo en el enlace.")
        except Exception as e:
            await processing_msg.edit(content=f"🔥 Error durante el proceso: {e}")
        finally:
            if video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                    print(f"🧹 Archivo local '{video_path}' eliminado.")
                except OSError as e:
                    print(f"🔥 Error al eliminar el archivo: {e}")


def setup(bot):
    bot.add_cog(EventsCog(bot))