import discord
from discord.ext import commands
import asyncio
import os


class TerminalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None

    @commands.Cog.listener()
    async def on_ready(self):
        print('⚙️  Cog de Terminal cargado y listo.')
        self.bot.loop.create_task(self.terminal_control())

    async def terminal_control(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            try:
                command_input = await asyncio.to_thread(input, "Comando > ")
                parts = command_input.strip().split()

                if not parts:
                    continue

                command = parts[0].lower()
                args = parts[1:]

                if command == "ayuda":
                    print("\n--- Comandos Disponibles ---")
                    print("escribir <ID_canal_texto> <mensaje>   - Envía un mensaje a un canal.")
                    print("entrar <ID_canal_voz>                  - Se une a un canal de voz.")
                    print("audio <ruta_del_archivo.mp3>          - Reproduce un archivo de audio.")
                    print("salir                                 - Se desconecta del canal de voz.")
                    print("terminar                              - Apaga el bot.")
                    print("--------------------------\n")

                elif command == "escribir":
                    if len(args) < 2:
                        print("❌ Uso: escribir <ID_canal_texto> <mensaje>")
                        continue

                    channel_id = int(args[0])
                    channel = self.bot.get_channel(channel_id)

                    if isinstance(channel, discord.TextChannel):
                        await channel.send(" ".join(args[1:]))
                        print(f"✅ Mensaje enviado al canal '{channel.name}'.")
                    else:
                        print(f"❌ No se encontró un canal de texto con el ID {channel_id}.")

                elif command == "entrar":
                    if len(args) < 1:
                        print("❌ Uso: entrar <ID_canal_voz>")
                        continue

                    channel_id = int(args[0])
                    channel = self.bot.get_channel(channel_id)

                    if isinstance(channel, discord.VoiceChannel):
                        if self.voice_client and self.voice_client.is_connected():
                            await self.voice_client.move_to(channel)
                        else:
                            self.voice_client = await channel.connect()
                        print(f"✅ Conectado al canal de voz '{channel.name}'.")
                    else:
                        print(f"❌ No se encontró un canal de voz con el ID {channel_id}.")

                elif command == "audio":
                    if len(args) < 1:
                        print("❌ Uso: audio <ruta_del_archivo>")
                        continue

                    if not self.voice_client or not self.voice_client.is_connected():
                        print("❌ El bot no está en un canal de voz. Usa 'entrar' primero.")
                        continue

                    audio_path = " ".join(args)
                    if not os.path.exists(audio_path):
                        print(f"❌ El archivo '{audio_path}' no existe.")
                        continue

                    if self.voice_client.is_playing():
                        self.voice_client.stop()

                    source = discord.FFmpegPCMAudio(audio_path)
                    self.voice_client.play(source,
                                           after=lambda e: print('▶️ Reproducción finalizada.') if not e else print(
                                               f'🔥 Error en la reproducción: {e}'))
                    print(f"🎧 Reproduciendo: {audio_path}")

                elif command == "salir":
                    if self.voice_client and self.voice_client.is_connected():
                        await self.voice_client.disconnect()
                        self.voice_client = None
                        print("✅ Desconectado del canal de voz.")
                    else:
                        print("❌ El bot no está en ningún canal de voz.")

                elif command == "terminar":
                    print("🔌 Apagando el bot...")
                    if self.voice_client:
                        await self.voice_client.disconnect()
                    await self.bot.close()
                    break

                else:
                    print(f"❓ Comando '{command}' desconocido. Escribe 'ayuda'.")

            except ValueError:
                print("🔥 Error: El ID del canal debe ser un número.")
            except Exception as e:
                print(f"🔥 Ocurrió un error inesperado: {e}")


def setup(bot):
    bot.add_cog(TerminalCog(bot))