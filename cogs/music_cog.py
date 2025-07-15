# cogs/music_cog.py
import discord
from discord.ext import commands
import asyncio
from collections import deque
from utils.downloader import search_youtube
import datetime
import logging

log = logging.getLogger(__name__)


class MusicCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.queues = {}
        self.current_song = {}

    def get_queue(self, guild_id: int):
        if guild_id not in self.queues:
            self.queues[guild_id] = deque()
        return self.queues[guild_id]

    async def play_next_song(self, ctx: discord.ApplicationContext):
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)

        if not queue:
            log.info(f"[{ctx.guild.name}] La cola de reproducción ha terminado.")
            await ctx.send("✅ La cola de reproducción ha terminado.")
            self.current_song.pop(guild_id, None)
            return

        song_info = queue.popleft()
        self.current_song[guild_id] = song_info
        log.info(f"[{ctx.guild.name}] Reproduciendo: {song_info['title']}")

        stream_url = song_info['stream_url']
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                          'options': '-vn'}

        ctx.voice_client.play(
            discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS),
            after=lambda e: self.handle_after_play(e, ctx)
        )

        embed = discord.Embed(title="🎵 Ahora Suena",
                              description=f"**{song_info['title']}**\npor *{song_info['uploader']}*",
                              color=discord.Color.green())
        await ctx.send(embed=embed)

    def handle_after_play(self, error, ctx):
        if error:
            log.error(f"[{ctx.guild.name}] Error durante la reproducción: {error}")

        log.info(f"[{ctx.guild.name}] Canción terminada, llamando a play_next_song.")
        self.bot.loop.create_task(self.play_next_song(ctx))

    @commands.slash_command(name="play", description="Reproduce una canción de YouTube o la añade a la cola.")
    async def play(self, ctx: discord.ApplicationContext, cancion: str):
        if not ctx.author.voice:
            await ctx.respond("❌ Debes estar en un canal de voz para usar este comando.", ephemeral=True)
            return

        await ctx.defer()  # El bot piensa mientras busca

        # --- ¡AQUÍ ESTÁ LA CORRECCIÓN DEL LAG! ---
        # Ejecutamos la búsqueda (que es bloqueante) en un hilo separado
        loop = asyncio.get_running_loop()
        song_info = await loop.run_in_executor(None, lambda: search_youtube(cancion))

        if not song_info or not song_info['stream_url']:
            log.warning(f"No se pudo encontrar la canción: '{cancion}'")
            await ctx.followup.send("❌ No se pudo encontrar la canción o la URL del streaming.")
            return

        voice_channel = ctx.author.voice.channel
        if not ctx.voice_client:
            await voice_channel.connect()
        elif ctx.voice_client.channel != voice_channel:
            await ctx.voice_client.move_to(voice_channel)

        queue = self.get_queue(ctx.guild.id)
        queue.append(song_info)
        log.info(f"[{ctx.guild.name}] Añadido a la cola por {ctx.author}: {song_info['title']}")

        if not ctx.voice_client.is_playing():
            await ctx.followup.send(f"▶️ Añadido a la cola: **{song_info['title']}**. Iniciando reproducción...")
            await self.play_next_song(ctx)
        else:
            await ctx.followup.send(f"✅ Añadido a la cola: **{song_info['title']}**.")

    # ... (El resto de comandos como /skip, /stop, etc., se mantienen igual)
    # ... (Puedes añadir logs dentro de ellos si lo deseas)


def setup(bot):
    bot.add_cog(MusicCog(bot))