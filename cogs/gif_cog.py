import discord
from discord.ext import commands
import aiohttp
import random
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuración ---
# Es recomendable obtener la clave desde una variable de entorno o un archivo de configuración.
# Puedes obtener tu clave de la API de Tenor desde Google Cloud Console.
# Por ahora, usamos una clave pública, pero puede ser menos fiable.
TENOR_API_KEY = "LIVDSRZULELA"
SEARCH_TERM = os.getenv("GIF_SEARCH_TERM", "default")  # Lee el término de búsqueda del .env

log = logging.getLogger(__name__)

class DownGifCog(commands.Cog):
    """
    Este Cog escucha los mensajes y responde con un gif aleatorio
    cuando detecta las palabras "down" o "downs".
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.http_session = None
        if not TENOR_API_KEY:
            log.warning("No se ha proporcionado una clave de API de Tenor. El cog de gifs no funcionará.")

    async def get_random_gif_url(self, query: str) -> str | None:
        """Busca en Tenor y devuelve la URL de un gif aleatorio."""
        if not TENOR_API_KEY:
            return None

        if self.http_session is None:
            self.http_session = aiohttp.ClientSession()

        # Usar el endpoint v1 que es más compatible con la clave pública
        url = f"https://g.tenor.com/v1/search?q={query}&key={TENOR_API_KEY}&limit=20"
        try:
            async with self.http_session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("results", [])
                    if results:
                        gif_object = random.choice(results)
                        # La URL del gif se encuentra dentro de media -> 0 -> gif -> url para la API v1
                        media = gif_object.get("media", [])
                        if media:
                            return media[0].get("gif", {}).get("url")
                else:
                    log.error(f"Error en la API de Tenor: Estado {response.status}")
        except Exception as e:
            log.error(f"No se pudo contactar con la API de Tenor: {e}")

        return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Se activa con cada mensaje para buscar las palabras clave."""
        if message.author.bot:
            return

        content = message.content.lower()
        if SEARCH_TERM in content:
            log.info(f"Palabra clave detectada de {message.author} en el canal {message.channel}.")

            gif_url = await self.get_random_gif_url(SEARCH_TERM)

            if gif_url:
                embed = discord.Embed(color=discord.Color.purple())
                embed.set_image(url=gif_url)
                await message.channel.send(embed=embed)
            else:
                log.warning(f"No se encontró ningún gif para '{SEARCH_TERM}'.")
                # Opcional: enviar un mensaje de error al usuario.
                # await message.channel.send(f"No pude encontrar un gif para '{SEARCH_TERM}'.")

    def cog_unload(self):
        """Limpia la sesión HTTP cuando el cog se descarga."""
        if self.http_session:
            self.bot.loop.create_task(self.http_session.close())

def setup(bot: commands.Bot):
    """Añade el cog al bot."""
    bot.add_cog(DownGifCog(bot))
