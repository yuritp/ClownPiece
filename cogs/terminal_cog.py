import discord
from discord.ext import commands
import asyncio
import os
from utils.downloader import download_video


class TerminalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None

    @commands.Cog.listener()
    async def on_ready(self):
        # Evita que se inicie el bucle varias veces si hay reconexiones
        if not hasattr(self, 'terminal_task') or self.terminal_task.done():
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
                    print(f"❓ Comando '{command}' desconocido. Escribe 'ayuda'.")
            except Exception as e:
                print(f"🔥 Ocurrió un error en la terminal: {e}")

    def print_help(self):
        print("\n--- Comandos de Terminal Disponibles ---")
        print("escribir <ID_canal> <mensaje>   - Envía un mensaje.")
        print("entrar <ID_canal_voz>           - Se une a un canal de voz.")
        print("audio <ruta_local_o_url>        - Reproduce un audio en el canal de voz.")
        print("salir                           - Se desconecta del canal de voz.")
        print("terminar                        - Apaga el bot.")
        print("--------------------------------------\n")

    async def handle_escribir(self, args):
        if len(args) < 2: return print("❌ Uso: escribir <ID_canal> <mensaje>")
        channel = self.bot.get_channel(int(args[0]))
        if isinstance(channel, discord.TextChannel):
            await channel.send(" ".join(args[1:]))
            print(f"✅ Mensaje enviado a '{channel.name}'.")

    async def handle_entrar(self, args):
        if not args: return print("❌ Uso: entrar <ID_canal_voz>")
        channel = self.bot.get_channel(int(args[0]))
        if isinstance(channel, discord.VoiceChannel):
            if self.voice_client and self.voice_client.is_connected():
                await self.voice_client.move_to(channel)
            else:
                self.voice_client = await channel.connect()
            print(f"✅ Conectado a '{channel.name}'.")

    async def handle_audio(self, args):
        if not args: return print("❌ Uso: audio <ruta_local_o_url>")
        if not self.voice_client or not self.voice_client.is_connected():
            return print("❌ El bot no está en un canal de voz.")

        path = " ".join(args)
        source = None
        if os.path.exists(path):
            source = discord.FFmpegPCMAudio(path)
        else:  # Asume que es una URL
            video_path = download_video(path)
            if video_path:
                source = discord.FFmpegPCMAudio(video_path)

        if source:
            self.voice_client.play(source, after=lambda e: print('▶️ Reproducción finalizada.') if not e else None)
            print(f"🎧 Reproduciendo...")
        else:
            print("❌ No se pudo encontrar el audio o descargar el vídeo.")

    async def handle_salir(self):
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
            print("✅ Desconectado.")

    async def handle_terminar(self):
        print("🔌 Apagando el bot...")
        if self.voice_client:
            await self.voice_client.disconnect()
        await self.bot.close()


def setup(bot):
    bot.add_cog(TerminalCog(bot))