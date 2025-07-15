import discord
from discord.ext import commands, tasks
import logging
import datetime
import re
import asyncio

log = logging.getLogger(__name__)


class UtilityCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.reminders = []
        self.check_reminders.start()

    # --- COMANDO DE ENCUESTAS ---
    @commands.slash_command(name="poll", description="Crea una encuesta con hasta 10 opciones.")
    async def poll(self,
                   ctx: discord.ApplicationContext,
                   pregunta: str,
                   opciones: str
                   ):
        log.info(f"Comando /poll usado por {ctx.author} con la pregunta: '{pregunta}'")
        opciones_lista = [op.strip() for op in opciones.split(';') if op.strip()]

        if len(opciones_lista) < 2 or len(opciones_lista) > 10:
            await ctx.respond("❌ Debes proporcionar entre 2 y 10 opciones, separadas por punto y coma (;).",
                              ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📊 ENCUESTA: {pregunta}",
            description="\n\n".join(f"{i + 1}️⃣ {op}" for i, op in enumerate(opciones_lista)),
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Encuesta creada por {ctx.author.display_name}")

        poll_message = await ctx.respond(embed=embed)
        # Añadimos las reacciones para que los usuarios voten
        for i in range(len(opciones_lista)):
            await poll_message.add_reaction(f"{i + 1}\u20e3")

    # --- SISTEMA DE RECORDATORIOS ---
    @commands.slash_command(name="remindme", description="Establece un recordatorio.")
    async def remindme(self,
                       ctx: discord.ApplicationContext,
                       tiempo: str,
                       recordatorio: str
                       ):
        log.info(f"Comando /remindme usado por {ctx.author}: '{recordatorio}' en '{tiempo}'")
        seconds = self.parse_time(tiempo)
        if seconds is None:
            await ctx.respond("❌ Formato de tiempo inválido. Usa (s, m, h, d). Ejemplo: `30m` o `1h`.", ephemeral=True)
            return

        future_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
        self.reminders.append((ctx.author.id, future_time, recordatorio))

        await ctx.respond(f"✅ ¡Entendido! Te recordaré sobre **'{recordatorio}'** en {tiempo}.", ephemeral=True)

    @tasks.loop(seconds=5)
    async def check_reminders(self):
        now = datetime.datetime.utcnow()
        # Creamos una copia para poder modificar la lista original mientras iteramos
        for r in list(self.reminders):
            user_id, fire_time, text = r
            if fire_time <= now:
                try:
                    user = await self.bot.fetch_user(user_id)
                    await user.send(f"⏰ **Recordatorio:** {text}")
                    log.info(f"Recordatorio enviado a {user.name}: '{text}'")
                except Exception as e:
                    log.error(f"No se pudo enviar el recordatorio al usuario {user_id}", exc_info=e)
                finally:
                    self.reminders.remove(r)

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

    def parse_time(self, time_str: str) -> int | None:
        match = re.match(r"(\d+)\s*(s|m|h|d)", time_str.lower())
        if not match: return None
        value, unit = int(match.group(1)), match.group(2)
        if unit == 's': return value
        if unit == 'm': return value * 60
        if unit == 'h': return value * 3600
        if unit == 'd': return value * 86400
        return None


def setup(bot):
    bot.add_cog(UtilityCog(bot))