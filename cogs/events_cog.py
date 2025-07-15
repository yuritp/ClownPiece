import discord
from discord.ext import commands
import re
import yt_dlp
import asyncio
import os


class EventsCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        match = re.search(r'https?://(twitter|x)\.com/\w+/status/\d+', message.content)
        if match:
            await self._process_twitter_link(match.group(0), message.channel)

    async def _process_twitter_link(self, url: str, channel: discord.TextChannel,
                                    original_message: discord.Message = None):
        """
        Descarga un vídeo de una URL de Twitter/X, lo envía a un canal y limpia el archivo local.
        """
        if original_message:
            processing_msg = original_message
            await processing_msg.edit(content=f"{processing_msg.content}\n\n*📎 Procesando vídeo...*")
        else:
            processing_msg = await channel.send(f"📎Procesando vídeo...")

        video_path = None
        try:
            loop = asyncio.get_running_loop()
            video_path = await loop.run_in_executor(None, lambda: self.download_video(url))

            if video_path and os.path.exists(video_path):
                # --- LÍNEA MODIFICADA ---
                # Ahora solo envía el archivo, sin texto adicional.
                await channel.send(file=discord.File(video_path))

                # Limpiamos el mensaje de "procesando"
                if original_message:
                    # Elimina la línea de "procesando" del mensaje original
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
                    print(f"🧹 Archivo local '{video_path}' eliminado correctamente.")
                except OSError as e:
                    print(f"🔥 Error al intentar eliminar el archivo local: {e}")

    def download_video(self, url):
        os.makedirs('downloads', exist_ok=True)
        ydl_opts = {
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'format': 'best[ext=mp4][height<=1080]/best[ext=mp4]/best',
            'noplaylist': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        except yt_dlp.utils.DownloadError:
            return None


def setup(bot):
    bot.add_cog(EventsCog(bot))