# cogs/commands_cog.py
import discord
from discord.ext import commands

class CommandsCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.slash_command(name="enviar", description="Envía un mensaje o un archivo a un canal.")
    async def enviar(
        self,
        ctx: discord.ApplicationContext,
        canal: discord.TextChannel,
        mensaje: discord.Option(str, "El texto que quieres enviar.", required=False),
        archivo: discord.Option(discord.Attachment, "El archivo que quieres adjuntar.", required=False)
    ):
        if not mensaje and not archivo:
            await ctx.respond("❌ Debes proporcionar al menos un mensaje o un archivo.", ephemeral=True)
            return

        try:
            file_to_send = await archivo.to_file() if archivo else None
            await canal.send(content=mensaje, file=file_to_send)
            await ctx.respond(f"✅ Contenido enviado a {canal.mention}.", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"🔥 Ocurrió un error: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(CommandsCog(bot))