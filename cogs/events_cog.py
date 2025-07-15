import discord
from discord.ext import commands
import re
import os
import datetime  # Necesario para las marcas de tiempo en los embeds
import logging
from config import Config
from utils.downloader import download_video

# Obtenemos un logger específico para este módulo
log = logging.getLogger(__name__)


class EventsCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    # --- LISTENER PRINCIPAL DE MENSAJES ---

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Se activa con cada mensaje y revisa si contiene un enlace de X/Twitter.
        """
        # Ignora los mensajes del propio bot para evitar bucles
        if message.author.bot:
            return

        # Busca un enlace que coincida con el patrón de X/Twitter
        match = re.search(r'https?://(twitter|x)\.com/\w+/status/\d+', message.content)
        if match:
            url = match.group(0)
            log.info(f"Enlace de X/Twitter detectado en el mensaje de {message.author}: {url}")
            # Llama a la función de procesamiento de vídeo
            await self.process_twitter_link(url, message.channel)

    # --- LISTENERS PARA EL LOG DE AUDITORÍA ---

    async def get_audit_log_channel(self):
        """Función de ayuda para obtener el canal de logs configurado."""
        return self.bot.get_channel(Config.AUDIT_LOG_CHANNEL_ID)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """
        Se activa cuando un mensaje es eliminado.
        """
        # Ignora mensajes del bot o mensajes sin texto (ej. solo un embed o una imagen)
        if message.author.bot or not message.content:
            return

        log_channel = await self.get_audit_log_channel()
        if not log_channel: return

        log.info(
            f"Mensaje de {message.author} eliminado en #{message.channel.name}. Registrando en el canal de auditoría.")

        embed = discord.Embed(
            title="🗑️ Mensaje Eliminado",
            description=f"**Autor:** {message.author.mention}\n**Canal:** {message.channel.mention}",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(name="Contenido", value=f"```{message.content}```", inline=False)
        embed.set_footer(text=f"ID del Autor: {message.author.id}")
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """
        Se activa cuando un mensaje es editado.
        """
        # Ignora ediciones del bot, mensajes sin cambios o mensajes sin texto
        if before.author.bot or before.content == after.content:
            return

        log_channel = await self.get_audit_log_channel()
        if not log_channel: return

        log.info(f"Mensaje de {after.author} editado en #{after.channel.name}. Registrando en el canal de auditoría.")

        embed = discord.Embed(
            title="✏️ Mensaje Editado",
            description=f"**Autor:** {after.author.mention}\n**Canal:** {after.channel.mention}\n[Ir al mensaje]({after.jump_url})",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(name="Antes", value=f"```{before.content or 'N/A'}```", inline=False)
        embed.add_field(name="Después", value=f"```{after.content or 'N/A'}```", inline=False)
        embed.set_footer(text=f"ID del Autor: {after.author.id}")
        await log_channel.send(embed=embed)

    # --- FUNCIÓN DE AYUDA PARA PROCESAR VÍDEOS ---

    async def process_twitter_link(self, url: str, channel: discord.TextChannel,
                                   original_message: discord.Message = None):
        """
        Descarga el vídeo, lo envía al canal y limpia los archivos locales.
        """
        if original_message:
            processing_msg = original_message
            await processing_msg.edit(content=f"{processing_msg.content}\n\n*📎 Procesando vídeo...*")
        else:
            processing_msg = await channel.send(f"📎 Enlace detectado. Procesando vídeo...")

        video_path = None
        try:
            video_path = download_video(url)

            if video_path and os.path.exists(video_path):
                log.info(f"Vídeo de {url} descargado en '{video_path}'. Enviando a Discord.")
                await channel.send(file=discord.File(video_path))

                # Limpia el mensaje de "procesando"
                if original_message:
                    clean_content = re.sub(r'\n\n\*📎 Procesando vídeo...\*', '', processing_msg.content)
                    await processing_msg.edit(content=clean_content)
                else:
                    await processing_msg.delete()
            elif video_path is None:
                log.warning(f"No se encontró vídeo en el enlace: {url}")
                await processing_msg.edit(content="🤔 No se encontró un vídeo en el enlace.")
        except Exception as e:
            log.error(f"Error procesando el enlace de Twitter {url}", exc_info=e)
            await processing_msg.edit(content=f"🔥 Error durante el proceso: {e}")
        finally:
            # Se asegura de que el archivo descargado se elimine siempre
            if video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                    log.info(f"🧹 Archivo local '{video_path}' eliminado.")
                except OSError as e:
                    log.error(f"🔥 Error al eliminar el archivo local '{video_path}'", exc_info=e)


def setup(bot):
    bot.add_cog(EventsCog(bot))