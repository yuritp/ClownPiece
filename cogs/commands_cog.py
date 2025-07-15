import discord
from discord.ext import commands


class CommandsCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    # Comando para enviar texto y archivos a un canal específico
    @commands.slash_command(name="enviar", description="Envía un mensaje o un archivo a un canal.")
    async def enviar(
            self,
            ctx: discord.ApplicationContext,
            canal: discord.TextChannel,
            mensaje: discord.Option(str, "El texto que quieres enviar.", required=False),
            archivo: discord.Option(discord.Attachment, "El archivo que quieres adjuntar.", required=False)
    ):
        # Comprueba que se haya proporcionado al menos un mensaje o un archivo
        if not mensaje and not archivo:
            await ctx.respond("❌ Debes proporcionar al menos un mensaje o un archivo.", ephemeral=True)
            return

        try:
            # Prepara el archivo para ser enviado si existe
            file_to_send = await archivo.to_file() if archivo else None

            # Envía el contenido al canal especificado
            await canal.send(content=mensaje, file=file_to_send)

            # Responde al usuario que el comando se ejecutó correctamente
            await ctx.respond(f"✅ Contenido enviado al canal {canal.mention}.", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"🔥 Ocurrió un error: {e}", ephemeral=True)

    # Comando para reproducir audio
    @commands.slash_command(name="reproducir", description="Reproduce un archivo de audio en un canal de voz.")
    async def reproducir(
            self,
            ctx: discord.ApplicationContext,
            canal_voz: discord.VoiceChannel,
            url_o_ruta: discord.Option(str, "La URL (YouTube) o ruta local del archivo de audio.")
    ):
        # Conectar al canal de voz
        try:
            voice_client = await canal_voz.connect()
        except Exception as e:
            await ctx.respond(f"🔥 No se pudo conectar al canal de voz: {e}", ephemeral=True)
            return

        # Reproducir el audio
        try:
            source = await discord.FFmpegOpusAudio.from_probe(url_o_ruta)
            voice_client.play(source)
            await ctx.respond(f"🎧 Reproduciendo en {canal_voz.mention}.", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"🔥 Error al reproducir el audio: {e}", ephemeral=True)
            await voice_client.disconnect()


def setup(bot):
    bot.add_cog(CommandsCog(bot))