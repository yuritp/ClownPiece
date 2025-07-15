import discord
from discord.ext import commands
import logging

log = logging.getLogger(__name__)

class CommandsCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    info_group = discord.SlashCommandGroup("info", "Comandos para obtener información.")
    voice_group = discord.SlashCommandGroup("voz", "Comandos para controlar el bot en canales de voz.")

    @info_group.command(name="servidor", description="Muestra información del servidor actual.")
    async def servidor(self, ctx: discord.ApplicationContext):
        log.info(f"Comando /info servidor ejecutado por {ctx.author} en '{ctx.guild.name}'.")
        guild = ctx.guild
        embed = discord.Embed(title=f"ℹ️ Información de {guild.name}", color=discord.Color.blue())
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="ID del Servidor", value=guild.id, inline=False)
        embed.add_field(name="Propietario", value=guild.owner.mention, inline=True)
        embed.add_field(name="Miembros", value=guild.member_count, inline=True)
        embed.add_field(name="Fecha de Creación", value=guild.created_at.strftime("%d/%m/%Y"), inline=False)
        await ctx.respond(embed=embed)

    @info_group.command(name="usuario", description="Muestra información de un usuario.")
    async def usuario(self, ctx: discord.ApplicationContext, miembro: discord.Option(discord.Member, "Elige un miembro", required=False)):
        miembro = miembro or ctx.author
        log.info(f"Comando /info usuario ejecutado por {ctx.author} para ver a {miembro.name}.")
        embed = discord.Embed(title=f"👤 Información de {miembro.display_name}", color=miembro.color)
        embed.set_thumbnail(url=miembro.display_avatar.url)
        embed.add_field(name="Nombre", value=miembro.name, inline=True)
        embed.add_field(name="Apodo", value=miembro.nick or "Ninguno", inline=True)
        embed.add_field(name="ID de Usuario", value=miembro.id, inline=False)
        embed.add_field(name="Se unió al servidor", value=miembro.joined_at.strftime("%d/%m/%Y"), inline=False)
        roles = [role.mention for role in miembro.roles if role.name != "@everyone"]
        embed.add_field(name="Roles", value=", ".join(roles) if roles else "Ninguno", inline=False)
        await ctx.respond(embed=embed)

    @voice_group.command(name="unirse", description="Hace que el bot se una a un canal de voz.")
    async def unirse(self, ctx: discord.ApplicationContext, canal: discord.Option(discord.VoiceChannel, "Canal de voz al que unirse")):
        log.info(f"Comando /voz unirse ejecutado por {ctx.author} para el canal '{canal.name}'.")
        try:
            await canal.connect()
            await ctx.respond(f"✅ Conectado a {canal.mention}", ephemeral=True)
        except Exception as e:
            log.error(f"Error en /voz unirse: {e}")
            await ctx.respond(f"🔥 Error al conectar: {e}", ephemeral=True)

    @voice_group.command(name="salir", description="Desconecta el bot del canal de voz.")
    async def salir(self, ctx: discord.ApplicationContext):
        log.info(f"Comando /voz salir ejecutado por {ctx.author}.")
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.respond("👋 Desconectado del canal de voz.", ephemeral=True)
        else:
            await ctx.respond("❌ No estoy en ningún canal de voz.", ephemeral=True)

def setup(bot):
    bot.add_cog(CommandsCog(bot))