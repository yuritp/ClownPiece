import asyncio

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
        self.active_polls = {}

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
        """Muestra el avatar de un usuario (o el tuyo si no se especifica)."""
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

    @commands.slash_command(name="poll", description="Crea una encuesta con opciones.")
    async def poll(self, ctx: discord.ApplicationContext,
                   pregunta: discord.Option(str, "La pregunta de la encuesta."),
                   opcion1: discord.Option(str, "Primera opción."),
                   opcion2: discord.Option(str, "Segunda opción."),
                   opcion3: discord.Option(str, "Tercera opción.", required=False),
                   opcion4: discord.Option(str, "Cuarta opción.", required=False),
                   opcion5: discord.Option(str, "Quinta opción.", required=False),
                   duracion: discord.Option(int, "Duración de la encuesta en minutos (0 para indefinido).", default=0)
                   ):
        """Crea una encuesta interactiva con reacciones."""
        log.info(f"Comando /poll usado por {ctx.author}: '{pregunta}'")

        options = [opcion1, opcion2, opcion3, opcion4, opcion5]
        valid_options = [opt for opt in options if opt is not None]

        if len(valid_options) < 2:
            return await ctx.respond("❌ Necesitas al menos dos opciones para una encuesta.", ephemeral=True)

        emoji_map = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣"}

        description = f"**{pregunta}**\n\n"
        for i, opt in enumerate(valid_options):
            description += f"{emoji_map[i + 1]} {opt}\n"

        if duracion > 0:
            description += f"\n_La encuesta finalizará en {duracion} minutos._"
        else:
            description += "\n_Esta encuesta no tiene límite de tiempo._"

        embed = discord.Embed(
            title="📊 Nueva Encuesta",
            description=description,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Encuesta iniciada por {ctx.author.display_name}",
                         icon_url=ctx.author.display_avatar.url)

        poll_message = await ctx.respond(embed=embed)
        sent_message = await poll_message.original_response()

        for i in range(len(valid_options)):
            await sent_message.add_reaction(emoji_map[i + 1])

        if duracion > 0:
            self.active_polls[sent_message.id] = {
                "ctx": ctx,
                "message": sent_message,
                "end_time": time.time() + (duracion * 60)
            }
            self.bot.loop.create_task(self._end_poll_after_delay(sent_message.id, duracion * 60))

    async def _end_poll_after_delay(self, message_id: int, delay_seconds: int):
        """Espera el tiempo especificado y finaliza la encuesta."""
        await asyncio.sleep(delay_seconds)

        if message_id not in self.active_polls:
            return

        poll_data = self.active_polls.pop(message_id)
        ctx = poll_data["ctx"]
        message = poll_data["message"]

        log.info(f"Finalizando encuesta {message.id} automáticamente.")
        await self._finalize_poll(ctx, message)

    async def _finalize_poll(self, ctx: discord.ApplicationContext, message: discord.Message):
        """Calcula y muestra los resultados de la encuesta."""
        try:
            message = await message.channel.fetch_message(message.id)

            emoji_map = {"1️⃣": "1️⃣", "2️⃣": "2️⃣", "3️⃣": "3️⃣", "4️⃣": "4️⃣", "5️⃣": "5️⃣"}

            results = {}
            for reaction in message.reactions:
                if str(reaction.emoji) in emoji_map.values():
                    users = [user async for user in reaction.users() if user != self.bot.user]
                    results[str(reaction.emoji)] = len(users)

            sorted_results = sorted(results.items(), key=lambda item: item[1], reverse=True)

            original_embed = message.embeds[0]
            original_description = original_embed.description
            question_match = original_description.split('\n\n')[0]
            original_options = original_description.split('\n\n')[1].split('\n')

            results_description = f"**Resultados de la encuesta: {question_match}**\n\n"

            emoji_to_option_text = {}
            for line in original_options:
                match = discord.utils.find(lambda emoji_key: line.startswith(emoji_key), emoji_map.values())
                if match:
                    emoji_to_option_text[match] = line.replace(match, '').strip()

            if not sorted_results:
                results_description += "No hubo votos."
            else:
                total_votes = sum(results.values())
                for emoji, count in sorted_results:
                    option_text = emoji_to_option_text.get(emoji, "Opción Desconocida")
                    percentage = (count / total_votes * 100) if total_votes > 0 else 0
                    results_description += f"{emoji} **{option_text}**: `{count}` votos (`{percentage:.1f}%)`\n"

            results_embed = discord.Embed(
                title="✅ Encuesta Finalizada",
                description=results_description,
                color=discord.Color.green()
            )
            results_embed.set_footer(
                text=f"Encuesta iniciada por {original_embed.footer.text.replace('Encuesta iniciada por ', '')}")

            await message.reply(embed=results_embed)
            await message.clear_reactions()

        except Exception as e:
            log.error(f"Error al finalizar la encuesta {message.id}: {e}", exc_info=True)
            await ctx.send("❌ Hubo un error al calcular los resultados de la encuesta.", ephemeral=True)


def setup(bot):
    """Función de configuración que Discord.py usa para añadir el cog."""
    bot.add_cog(FunCog(bot))