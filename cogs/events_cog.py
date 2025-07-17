import discord
from discord.ext import commands
import re
import os
import datetime
import logging

# --- IMPORTACIONES LOCALES ---
from config import Config
from database import database_manager as db

# Obtenemos un logger específico para este módulo
log = logging.getLogger(__name__)


class EventsCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    async def get_audit_log_channel(self):
        """Obtiene el canal de logs de auditoría configurado en el bot."""
        return self.bot.get_channel(Config.AUDIT_LOG_CHANNEL_ID)

    # --- LISTENERS DE AUDITORÍA ---
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Registra y reporta la eliminación de mensajes."""
        if message.author.bot or not message.content:
            return

        db.add_log("MESSAGE_DELETE", message.author.id, message.channel.id, message.content)

        log_channel = await self.get_audit_log_channel()
        if not log_channel: return

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
        """Registra y reporta la edición de mensajes."""
        if before.author.bot or before.content == after.content:
            return

        details = f"Antes: {before.content or 'N/A'}"
        db.add_log("MESSAGE_EDIT", after.author.id, after.channel.id, after.content, details)

        log_channel = await self.get_audit_log_channel()
        if not log_channel: return

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

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        """Registra y reporta cambios de estado en canales de voz."""
        if member.bot: return

        log_channel = await self.get_audit_log_channel()
        embed = None

        # Usuario se conecta a un canal de voz
        if before.channel is None and after.channel is not None:
            db.add_log("VOICE_JOIN", member.id, after.channel.id)
            if log_channel:
                embed = discord.Embed(title="🎙️ Conexión a Voz",
                                      description=f"{member.mention} se conectó al canal de voz **{after.channel.name}**.",
                                      color=discord.Color.green())

        # Usuario se desconecta de un canal de voz
        elif before.channel is not None and after.channel is None:
            db.add_log("VOICE_LEAVE", member.id, before.channel.id)
            if log_channel:
                embed = discord.Embed(title="🎙️ Desconexión de Voz",
                                      description=f"{member.mention} se desconectó del canal de voz **{before.channel.name}**.",
                                      color=discord.Color.red())

        # Usuario se mueve entre canales de voz
        elif before.channel is not None and after.channel is not None and before.channel != after.channel:
            details = f"Desde: {before.channel.name} -> Hacia: {after.channel.name}"
            db.add_log("VOICE_MOVE", member.id, after.channel.id, details=details)
            if log_channel:
                embed = discord.Embed(title="🎙️ Movimiento en Voz",
                                      description=f"{member.mention} se movió de **{before.channel.name}** a **{after.channel.name}**.",
                                      color=discord.Color.blue())

        if log_channel and embed:
            embed.set_footer(text=f"ID del Usuario: {member.id}")
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await log_channel.send(embed=embed)



def setup(bot):
    bot.add_cog(EventsCog(bot))