import discord
from discord.ext import commands
import asyncio
import os
import logging
from utils.downloader import download_video

log = logging.getLogger(__name__)

class TerminalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None

    @commands.Cog.listener()
    async def on_ready(self):
        # Evita que se inicie el bucle varias veces si hay reconexiones
        if not hasattr(self, 'terminal_task') or self.terminal_task.done():
            log.info('⚙️  Cog de Terminal listo. Escribe "ayuda" en la consola para ver los comandos.')
            print('⚙️  Cog de Terminal listo. Escribe "ayuda" en la consola para ver los comandos.')
            self.terminal_task = self.bot.loop.create_task(self.terminal_control())

    async def terminal_control(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                command_input = await asyncio.to_thread(input, "Comando > ")
                parts = command_input.strip().split()
                if not parts: continue
                command, *args = parts
                command = command.lower()

                if command == "ayuda":
                    self.print_help()
                elif command == "escribir":
                    await self.handle_escribir(args)
                elif command == "entrar":
                    await self.handle_entrar(args)
                elif command == "audio":
                    await self.handle_audio(args)
                elif command == "salir":
                    await self.handle_salir()
                elif command == "terminar":
                    await self.handle_terminar()
                    break
                else:
                    log.warning(f"Comando '{command}' desconocido. Escribe 'ayuda'.")
                    print(f"❓ Comando '{command}' desconocido. Escribe 'ayuda'.")
            except Exception as e:
                log.error(f"Ocurrió un error en la terminal: {e}", exc_info=True)
                print(f"🔥 Ocurrió un error en la terminal: {e}")

    def print_help(self):
        help_text = (
            "\n--- Comandos de Terminal Disponibles ---\n"
            "escribir <ID_canal> <mensaje>   - Envía un mensaje.\n"
            "entrar <ID_canal_voz>           - Se une a un canal de voz.\n"
            "audio <ruta_local_o_url>        - Reproduce un audio en el canal de voz.\n"
            "salir                           - Se desconecta del canal de voz.\n"
            "terminar                        - Apaga el bot.\n"
            "--------------------------------------\n"
        )
        log.info("Mostrando ayuda de terminal.")
        print(help_text)

    async def handle_escribir(self, args):
        if len(args) < 2:
            log.warning("Uso incorrecto de 'escribir'.")
            print("❌ Uso: escribir <ID_canal> <mensaje>")
            return
        channel = self.bot.get_channel(int(args[0]))
        if isinstance(channel, discord.TextChannel):
            await channel.send(" ".join(args[1:]))
            log.info(f"Mensaje enviado a '{channel.name}'.")
            print(f"✅ Mensaje enviado a '{channel.name}'.")

    async def handle_entrar(self, args):
        if not args:
            log.warning("Uso incorrecto de 'entrar'.")
            print("❌ Uso: entrar <ID_canal_voz>")
            return
        channel = self.bot.get_channel(int(args[0]))
        if isinstance(channel, discord.VoiceChannel):
            if self.voice_client and self.voice_client.is_connected():
                await self.voice_client.move_to(channel)
            else:
                self.voice_client = await channel.connect()
            log.info(f"Conectado a '{channel.name}'.")
            print(f"✅ Conectado a '{channel.name}'.")

    async def handle_audio(self, args):
        if not args:
            log.warning("Uso incorrecto de 'audio'.")
            print("❌ Uso: audio <ruta_local_o_url>")
            return
        if not self.voice_client or not self.voice_client.is_connected():
            log.warning("El bot no está en un canal de voz.")
            print("❌ El bot no está en un canal de voz.")
            return

        path = " ".join(args)
        source = None
        if os.path.exists(path):
            source = discord.FFmpegPCMAudio(path)
            log.info(f"Reproduciendo audio local: {path}")
        else:  # Asume que es una URL
            video_path = download_video(path)
            if video_path:
                source = discord.FFmpegPCMAudio(video_path)
                log.info(f"Descargado y reproduciendo vídeo: {video_path}")
            else:
                log.error(f"No se pudo descargar el vídeo de la URL: {path}")

        if source:
            self.voice_client.play(source, after=lambda e: log.info('▶️ Reproducción finalizada.') if not e else log.error(f"Error en reproducción: {e}"))
            print(f"🎧 Reproduciendo...")
        else:
            print("❌ No se pudo encontrar el audio o descargar el vídeo.")

    async def handle_salir(self):
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
            log.info("Desconectado del canal de voz.")
            print("✅ Desconectado.")

    async def handle_terminar(self):
        log.info("Apagando el bot por comando de terminal.")
        print("🔌 Apagando el bot...")
        if self.voice_client:
            await self.voice_client.disconnect()
        await self.bot.close()


def setup(bot):
    bot.add_cog(TerminalCog(bot))