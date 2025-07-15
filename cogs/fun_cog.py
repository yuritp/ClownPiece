import discord
from discord.ext import commands
import logging
import aiohttp

log = logging.getLogger(__name__)

class FunCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        # Inicializamos la sesión a None. Se creará solo cuando se necesite.
        self.http_session = None

    # --- MÉTODO DE AYUDA PARA LA SESIÓN ---
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
        Función de ayuda para hacer peticiones a APIs usando la sesión segura.
        """
        # Obtenemos la sesión usando nuestro nuevo método de ayuda
        session = await self._get_session()
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            log.error(f"Error al hacer una petición a {url}", exc_info=e)
        return None

    @commands.slash_command(name="cat", description="¡Muestra una foto aleatoria de un gato!")
    async def cat(self, ctx: discord.ApplicationContext):
        log.info(f"Comando /cat usado por {ctx.author}.")
        data = await self.get_json("https://api.thecatapi.com/v1/images/search")
        if data and data[0]['url']:
            embed = discord.Embed(title="🐱 Miau!", color=discord.Color.blue())
            embed.set_image(url=data[0]['url'])
            await ctx.respond(embed=embed)
        else:
            await ctx.respond("❌ No se pudo obtener una foto de gatito en este momento.", ephemeral=True)

    @commands.slash_command(name="dog", description="¡Muestra una foto aleatoria de un perro!")
    async def dog(self, ctx: discord.ApplicationContext):
        log.info(f"Comando /dog usado por {ctx.author}.")
        data = await self.get_json("https://api.thedogapi.com/v1/images/search")
        if data and data[0]['url']:
            embed = discord.Embed(title="🐶 ¡Guau!", color=discord.Color.orange())
            embed.set_image(url=data[0]['url'])
            await ctx.respond(embed=embed)
        else:
            await ctx.respond("❌ No se pudo obtener una foto de perrito en este momento.", ephemeral=True)

    @commands.slash_command(name="joke", description="Cuenta un chiste.")
    async def joke(self, ctx: discord.ApplicationContext):
        log.info(f"Comando /joke usado por {ctx.author}.")
        data = await self.get_json("https://v2.jokeapi.dev/joke/Any?lang=es&type=single")
        if data and not data['error']:
            embed = discord.Embed(title="🤣 Un Chistecito", description=data['joke'], color=discord.Color.gold())
            await ctx.respond(embed=embed)
        else:
            await ctx.respond("❌ Me he quedado sin chistes por ahora.", ephemeral=True)

    @commands.slash_command(name="fact", description="Cuenta un dato curioso (en inglés).")
    async def fact(self, ctx: discord.ApplicationContext):
        log.info(f"Comando /fact usado por {ctx.author}.")
        data = await self.get_json("https://uselessfacts.jsph.pl/random.json?language=en")
        if data and data['text']:
            embed = discord.Embed(title="🧠 Dato Curioso", description=data['text'], color=discord.Color.teal())
            await ctx.respond(embed=embed)
        else:
            await ctx.respond("❌ No pude encontrar un dato curioso.", ephemeral=True)

def setup(bot):
    bot.add_cog(FunCog(bot))