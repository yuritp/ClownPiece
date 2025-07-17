import discord
from discord.ext import commands
import logging
import aiohttp
import time  # Para el comando ping
import re  # Necesario para la detección de la palabra "down"

log = logging.getLogger(__name__)


class FunCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.http_session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Crea una sesión de aiohttp si no existe, o devuelve la existente.
        Esto asegura que la sesión se cree dentro de un contexto asíncrono.
        """
        if self.http_session is None:
            log.info("Creando nueva sesión de aiohttp para FunCog.")
            self.http_session = aiohttp.ClientSession()
        return self.http_session

    def cog_unload(self):
        """
        Se asegura de que la sesión se cierre correctamente si el cog se descarga.
        """
        if self.http_session:
            self.bot.loop.create_task(self.http_session.close())
            log.info("Cerrando la sesión de aiohttp de FunCog.")

    async def get_json(self, url):
        """
        Función de ayuda para hacer peticiones a API usando la sesión segura.
        """
        session = await self._get_session()
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    log.warning(f"API request to {url} failed with status {response.status}")
        except Exception as e:
            log.error(f"Error al hacer una petición a {url}", exc_info=e)
        return None

    # --- Listener para el Easter Egg "down" ---
    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Maneja los mensajes para el Easter Egg 'down'.
        """
        # Ignora los mensajes del propio bot
        if message.author == self.bot.user:
            return

        # Ignora mensajes de bots (incluyendo otros bots, no solo el propio)
        if message.author.bot:
            return

        # --- Easter Egg "down" ---
        # re.search busca la palabra "down" como una palabra completa (case-insensitive)
        # Esto evita que reaccione a palabras como "download" o "downtime"
        if re.search(r'\bdown\b', message.content, re.IGNORECASE):
            log.info(
                f"Detectado 'down' en mensaje de {message.author.display_name} ({message.author.id}). Reaccionando con 😂.")
            try:
                await message.add_reaction("😂")  # El emoji de la cara con lágrimas de alegría
            except discord.HTTPException as e:
                log.error(f"No se pudo añadir la reacción 😂 al mensaje {message.id}: {e}")
            # No hay 'return' aquí, para que el bot pueda seguir procesando otros comandos
            # si el mensaje también contiene uno (aunque los slash commands ya se ignoran arriba).

    # --- Comandos Existentes (sin cambios, solo para contexto) ---

    @commands.slash_command(name="cat", description="¡Muestra una foto aleatoria de un gato!")
    async def cat(self, ctx: discord.ApplicationContext):
        log.info(f"Comando /cat usado por {ctx.author}.")
        await ctx.defer()  # Aplazar la respuesta
        data = await self.get_json("https://api.thecatapi.com/v1/images/search")
        if data and data[0].get('url'):
            embed = discord.Embed(title="🐱 Miau!", color=discord.Color.blue())
            embed.set_image(url=data[0]['url'])
            await ctx.followup.send(embed=embed)
        else:
            await ctx.followup.send("❌ No se pudo obtener una foto de gatito en este momento.", ephemeral=True)

    @commands.slash_command(name="dog", description="¡Muestra una foto aleatoria de un perro!")
    async def dog(self, ctx: discord.ApplicationContext):
        log.info(f"Comando /dog usado por {ctx.author}.")
        await ctx.defer()  # Aplazar la respuesta
        data = await self.get_json("https://api.thedogapi.com/v1/images/search")
        if data and data[0].get('url'):
            embed = discord.Embed(title="🐶 ¡Guau!", color=discord.Color.orange())
            embed.set_image(url=data[0]['url'])
            await ctx.followup.send(embed=embed)
        else:
            await ctx.followup.send("❌ No se pudo obtener una foto de perrito en este momento.", ephemeral=True)

    @commands.slash_command(name="joke", description="Cuenta un chiste.")
    async def joke(self, ctx: discord.ApplicationContext):
        log.info(f"Comando /joke usado por {ctx.author}.")
        await ctx.defer()  # Aplazar la respuesta
        data = await self.get_json("https://v2.jokeapi.dev/joke/Any?lang=es&type=single")
        if data and not data.get('error'):
            embed = discord.Embed(title="🤣 Un Chistecito", description=data['joke'], color=discord.Color.gold())
            await ctx.followup.send(embed=embed)
        else:
            await ctx.followup.send("❌ Me he quedado sin chistes por ahora.", ephemeral=True)

    @commands.slash_command(name="fact", description="Cuenta un dato curioso (en inglés).")
    async def fact(self, ctx: discord.ApplicationContext):
        log.info(f"Comando /fact usado por {ctx.author}.")
        await ctx.defer()  # Aplazar la respuesta
        data = await self.get_json("https://uselessfacts.jsph.pl/random.json?language=en")
        if data and data.get('text'):
            embed = discord.Embed(title="🧠 Dato Curioso", description=data['text'], color=discord.Color.teal())
            await ctx.followup.send(embed=embed)
        else:
            await ctx.followup.send("❌ No pude encontrar un dato curioso.", ephemeral=True)

    # --- Comandos Añadidos Anteriormente ---

    @commands.slash_command(name="ping", description="Muestra la latencia del bot en ms.")
    async def ping(self, ctx: discord.ApplicationContext):
        """Muestra la latencia del bot."""
        log.info(f"Comando /ping usado por {ctx.author}.")
        latency_ms = round(self.bot.latency * 1000)

        start_time = time.time()
        await ctx.defer(ephemeral=True)
        end_time = time.time()
        api_latency_ms = round((end_time - start_time) * 1000)

        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latencia del WebSocket: `{latency_ms}ms`\nLatencia de la API: `{api_latency_ms}ms`",
            color=discord.Color.green()
        )
        await ctx.followup.send(embed=embed)

    @commands.slash_command(name="avatar", description="Muestra el avatar de un usuario.")
    async def avatar(self, ctx: discord.ApplicationContext,
                     usuario: discord.Option(discord.Member, "Usuario cuyo avatar quieres ver", required=False)):
        log.info(f"Comando /avatar usado por {ctx.author} para {usuario if usuario else 'sí mismo'}.")

        target_user = usuario if usuario else ctx.author
        avatar_url = target_user.display_avatar.url

        embed = discord.Embed(
            title=f"Avatar de {target_user.display_name}",
            color=discord.Color.blurple()
        )
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        await ctx.respond(embed=embed)

def setup(bot):
    """Función de configuración que Discord.py usa para añadir el cog."""
    bot.add_cog(FunCog(bot))