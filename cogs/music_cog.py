import discord
from discord.ext import commands
import asyncio
from collections import deque
import datetime
import logging
import random
import os

# --- IMPORTACIONES LOCALES ---
# Asegúrate de que 'utils.downloader' y 'config' sean accesibles desde donde ejecutas tu main.py
from utils.downloader import search_youtube
from config import Config

log = logging.getLogger(__name__)

# Definimos la ruta de los audios aleatorios desde Config.
# Asumo que Config.RANDOM_AUDIO_PATH ya está definido como 'C:\Users\joelb\PycharmProjects\ClownPiece\random_audio'
# en tu archivo config.py
RANDOM_AUDIO_DIR = Config.RANDOM_AUDIO_PATH


class MusicCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.queues = {}
        self.current_song = {}
        self.inactivity_tasks = {}  # Tareas para la inactividad por gremio

    def get_queue(self, guild_id: int):
        """Obtiene o crea la cola de reproducción para un gremio."""
        if guild_id not in self.queues:
            self.queues[guild_id] = deque()
        return self.queues[guild_id]

    # --- LÓGICA DE INACTIVIDAD Y EASTER EGG ---

    def start_inactivity_check(self, guild: discord.Guild):
        """Inicia o reinicia el chequeo de inactividad para un gremio."""
        guild_id = guild.id

        # Cancela cualquier tarea de inactividad existente para este gremio
        if guild_id in self.inactivity_tasks and not self.inactivity_tasks[guild_id].done():
            self.inactivity_tasks[guild_id].cancel()
            log.info(f"[{guild.name}] Cancelada tarea de inactividad previa.")

        log.info(f"[{guild.name}] Iniciando chequeo de inactividad para easter egg (10s).")
        # Crea una nueva tarea para el bucle de inactividad
        self.inactivity_tasks[guild_id] = self.bot.loop.create_task(self.inactivity_loop(guild))

    def stop_inactivity_check(self, guild_id: int):
        """Detiene y elimina el chequeo de inactividad para un gremio."""
        if guild_id in self.inactivity_tasks and not self.inactivity_tasks[guild_id].done():
            self.inactivity_tasks[guild_id].cancel()
            log.info(f"[{guild_id}] Chequeo de inactividad detenido y limpiado.")
        self.inactivity_tasks.pop(guild_id, None)  # Asegurarse de limpiar el diccionario

    async def inactivity_loop(self, guild: discord.Guild):
        """
        Bucle de inactividad: espera 10s, reproduce el easter egg y desconecta.
        """
        voice_client = guild.voice_client
        if not voice_client or not voice_client.is_connected():
            log.warning(f"[{guild.name}] inactivity_loop llamado sin un cliente de voz conectado. Terminando.")
            self.stop_inactivity_check(guild.id)  # Asegurar limpieza
            return

        try:
            log.debug(f"[{guild.name}] Esperando 10 segundos de inactividad...")
            # Esperamos 10 segundos. Si la tarea es cancelada (por una nueva canción, stop, etc.), se interrumpe.
            await asyncio.sleep(10)

            # Re-verificar el estado después de la espera
            if not voice_client.is_connected():
                log.info(f"[{guild.name}] Bot desconectado durante la espera de inactividad. Terminando.")
                return
            if voice_client.is_playing():
                log.info(f"[{guild.name}] Se inició una reproducción durante la espera de inactividad. Terminando.")
                return

            log.info(f"[{guild.name}] 10 segundos de inactividad confirmados. Activando easter egg.")
            await self.play_random_audio(voice_client)  # Reproduce el easter egg y espera a que termine

            # Después de reproducir el easter egg, desconectar si sigue conectado
            if voice_client.is_connected():
                log.info(f"[{guild.name}] Easter egg terminado. Desconectando por inactividad del loop.")
                await voice_client.disconnect()

        except asyncio.CancelledError:
            log.info(f"[{guild.name}] Chequeo de inactividad cancelado (nueva canción, stop, etc.).")
        except Exception as e:
            log.error(f"[{guild.name}] Error inesperado en inactivity_loop: {e}", exc_info=True)
            if voice_client and voice_client.is_connected():  # Intentar desconectar en caso de error grave
                await voice_client.disconnect()
        finally:
            self.stop_inactivity_check(guild.id)  # Asegurarse de limpiar la tarea al finalizar (éxito o error)

    async def play_random_audio(self, voice_client: discord.VoiceClient):
        """
        Reproduce un audio aleatorio del directorio RANDOM_AUDIO_DIR y espera a que termine.
        """
        if not voice_client or not voice_client.is_connected():
            log.warning(f"[{voice_client.guild.name}] No hay cliente de voz conectado para reproducir audio aleatorio.")
            return

        try:
            audio_files = [f for f in os.listdir(RANDOM_AUDIO_DIR) if f.endswith(('.mp3', '.wav', '.ogg'))]
            if not audio_files:
                log.warning(f"[{voice_client.guild.name}] No se encontraron archivos de audio en {RANDOM_AUDIO_DIR}.")
                return

            random_file = os.path.join(RANDOM_AUDIO_DIR, random.choice(audio_files))
            log.info(f"[{voice_client.guild.name}] Reproduciendo easter egg: {random_file}")

            source = discord.FFmpegPCMAudio(random_file)
            finished = asyncio.Event()

            voice_client.play(source, after=lambda e: self.bot.loop.call_soon_threadsafe(finished.set))

            # Esperar un tiempo máximo para el audio, en caso de que 'after' no se llame
            try:
                # Usar un timeout razonable para la reproducción del easter egg
                await asyncio.wait_for(finished.wait(), timeout=30)  # Ej: 30 segundos como máximo
            except asyncio.TimeoutError:
                log.warning(
                    f"[{voice_client.guild.name}] Reproducción del easter egg excedió el tiempo de espera. Forzando detención.")
                voice_client.stop()

        except Exception as e:
            log.error(f"[{voice_client.guild.name}] Error al intentar reproducir el easter egg '{random_file}'.",
                      exc_info=e)
            if voice_client.is_playing():
                voice_client.stop()

    # --- LÓGICA DEL REPRODUCTOR PRINCIPAL ---

    async def play_next_song(self, ctx: discord.ApplicationContext):
        """Maneja la reproducción de la siguiente canción en la cola."""
        self.stop_inactivity_check(ctx.guild.id)  # Asegura que no haya chequeo de inactividad mientras suena la cola

        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        voice_client = ctx.voice_client  # Obtener el voice_client actual del contexto

        # Si no hay cliente de voz o no está conectado, salir
        if not voice_client or not voice_client.is_connected():
            log.warning(
                f"[{ctx.guild.name}] play_next_song llamado sin cliente de voz conectado. Terminando reproducción.")
            self.current_song.pop(guild_id, None)
            return

        if not queue:
            log.info(f"[{ctx.guild.name}] La cola de reproducción ha terminado.")
            await ctx.send("✅ La cola de reproducción ha terminado.")
            self.current_song.pop(guild_id, None)
            # Iniciar chequeo de inactividad SÓLO si el bot sigue conectado y la cola está vacía
            self.start_inactivity_check(ctx.guild)
            return

        song_info = queue.popleft()
        self.current_song[guild_id] = song_info
        log.info(f"[{ctx.guild.name}] Reproduciendo: {song_info['title']}")

        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                          'options': '-vn'}
        try:
            source = await discord.FFmpegOpusAudio.from_probe(song_info['stream_url'], **FFMPEG_OPTIONS)
            # El 'after' lambda necesita un loop.create_task para ejecutar la siguiente canción en el bucle de eventos
            voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.handle_after_play(e, ctx)))
            embed = discord.Embed(title="🎵 Ahora Suena",
                                  description=f"**{song_info['title']}**\npor *{song_info['uploader']}*",
                                  color=discord.Color.green())
            # Usa ctx.send() para enviar la actualización de la canción
            await ctx.send(embed=embed)
        except Exception as e:
            log.error(f"[{ctx.guild.name}] Error al intentar reproducir {song_info['title']}", exc_info=e)
            await ctx.send(f"🔥 No se pudo reproducir la canción: `{song_info['title']}`. Saltando a la siguiente.")
            await self.play_next_song(ctx)  # Intenta la siguiente canción en la cola

    async def handle_after_play(self, error, ctx: discord.ApplicationContext):
        """Callback ejecutado después de que una canción termina o hay un error."""
        if error:
            log.error(f"[{ctx.guild.name}] Error durante la reproducción: {error}")

        # Asegurarse de que el bot sigue conectado y no está reproduciendo activamente
        if ctx.voice_client and ctx.voice_client.is_connected() and not ctx.voice_client.is_playing():
            await self.play_next_song(ctx)  # Continúa con la siguiente canción o inicia chequeo de inactividad

    # --- COMANDOS SLASH ---

    @commands.slash_command(name="play", description="Reproduce una canción de YouTube o la añade a la cola.")
    async def play(self, ctx: discord.ApplicationContext, cancion: str):
        if not ctx.author.voice:
            return await ctx.respond("❌ Debes estar en un canal de voz para usar este comando.", ephemeral=True)

        self.stop_inactivity_check(ctx.guild.id)  # Detener cualquier chequeo de inactividad activo

        voice_client = ctx.voice_client
        # Conectar o mover el bot al canal de voz del autor
        if not voice_client:
            log.info(f"[{ctx.guild.name}] Conectando a {ctx.author.voice.channel.name}")
            try:
                voice_client = await ctx.author.voice.channel.connect(cls=discord.VoiceClient)
            except discord.ClientException as e:
                log.error(f"[{ctx.guild.name}] Error al conectar al canal de voz: {e}", exc_info=True)
                return await ctx.respond("❌ No se pudo conectar al canal de voz. Inténtalo de nuevo.", ephemeral=True)
        elif voice_client.channel != ctx.author.voice.channel:
            log.info(f"[{ctx.guild.name}] Moviendo a {ctx.author.voice.channel.name}")
            await voice_client.move_to(ctx.author.voice.channel)

        await ctx.defer()  # Aplaza la respuesta para dar tiempo a la búsqueda

        loop = asyncio.get_running_loop()
        song_info = await loop.run_in_executor(None, lambda: search_youtube(cancion))

        if not song_info or not song_info.get('stream_url'):
            log.warning(f"No se pudo encontrar la canción: '{cancion}'")
            return await ctx.followup.send("❌ No se pudo encontrar la canción o su URL.")

        queue = self.get_queue(ctx.guild.id)
        queue.append(song_info)
        log.info(f"[{ctx.guild.name}] Añadido a la cola por {ctx.author}: {song_info['title']}")

        if not voice_client.is_playing():
            # Si no está sonando, empezamos la reproducción
            await ctx.followup.send(f"▶️ **{song_info['title']}** añadido. Iniciando reproducción...")
            await self.play_next_song(ctx)
        else:
            # Si ya está sonando, solo añadimos a la cola
            await ctx.followup.send(f"✅ Añadido a la cola: **{song_info['title']}**.")

    @commands.slash_command(name="stop", description="Detiene la música, vacía la cola y desconecta el bot.")
    async def stop(self, ctx: discord.ApplicationContext):
        if not ctx.voice_client:
            return await ctx.respond("No estoy en un canal de voz.", ephemeral=True)

        self.stop_inactivity_check(ctx.guild.id)  # Asegura detener cualquier tarea de inactividad
        self.get_queue(ctx.guild.id).clear()  # Vaciar la cola
        self.current_song.pop(ctx.guild.id, None)  # Limpiar la canción actual
        ctx.voice_client.stop()  # Detener la reproducción actual

        if ctx.voice_client.is_connected():
            await ctx.voice_client.disconnect()
            log.info(f"[{ctx.guild.name}] Bot desconectado por comando /stop.")
        await ctx.respond("⏹️ Música detenida y bot desconectado.")

    @commands.slash_command(name="skip", description="Salta a la siguiente canción de la cola.")
    async def skip(self, ctx: discord.ApplicationContext):
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.respond("No hay ninguna canción sonando.", ephemeral=True)

        self.stop_inactivity_check(ctx.guild.id)  # Detener el chequeo de inactividad temporalmente
        ctx.voice_client.stop()  # Esto activará handle_after_play para la siguiente canción
        await ctx.respond("⏭️ Canción saltada.")

    @commands.slash_command(name="queue", description="Muestra la cola de canciones.")
    async def queue(self, ctx: discord.ApplicationContext):
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        current = self.current_song.get(guild_id)
        if not queue and not current:
            return await ctx.respond("No hay ninguna canción en la cola ni sonando actualmente.", ephemeral=True)

        embed = discord.Embed(title="📜 Cola de Reproducción", color=discord.Color.purple())

        if current:
            duration = str(datetime.timedelta(seconds=current.get('duration', 0)))
            embed.add_field(name="▶️ Sonando Ahora",
                            value=f"**{current['title']}**\n*{current['uploader']}* ({duration})", inline=False)

        if queue:
            queue_text = ""
            for i, song in enumerate(list(queue)[:10]):  # Mostrar solo las primeras 10 canciones
                queue_text += f"\n`{i + 1}.` {song['title']}"
            if len(queue) > 10:
                queue_text += f"\n... y {len(queue) - 10} más."

            if queue_text:  # Asegurarse de que hay texto para añadir el campo
                embed.add_field(name="⬇️ A Continuación", value=queue_text, inline=False)

        await ctx.respond(embed=embed)

    @commands.slash_command(name="nowplaying", description="Muestra la canción que está sonando.")
    async def nowplaying(self, ctx: discord.ApplicationContext):
        guild_id = ctx.guild.id
        current = self.current_song.get(guild_id)
        if not ctx.voice_client or not ctx.voice_client.is_playing() or not current:
            return await ctx.respond("No hay ninguna canción sonando.", ephemeral=True)

        duration = str(datetime.timedelta(seconds=current.get('duration', 0)))
        embed = discord.Embed(title="🎵 Sonando Ahora",
                              description=f"**{current['title']}**\npor *{current['uploader']}*",
                              color=discord.Color.blue())
        embed.add_field(name="Duración", value=duration)
        await ctx.respond(embed=embed)


def setup(bot):
    """Función de configuración que Discord.py usa para añadir el cog."""
    bot.add_cog(MusicCog(bot))