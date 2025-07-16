import discord
from discord.ext import commands
import logging
import psutil

log = logging.getLogger(__name__)

class ResourcesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="resources", description="Muestra el uso de recursos del bot.")
    @commands.is_owner()
    async def resources(self, ctx: discord.ApplicationContext):
        process = psutil.Process()
        cpu_usage = process.cpu_percent(interval=1)
        ram_usage = process.memory_info().rss / (1024 ** 2)  # Convertir a MB

        embed = discord.Embed(title="📊 Estado de Recursos del Bot", color=discord.Color.green())
        embed.add_field(name="Uso de CPU", value=f"{cpu_usage:.2f}%", inline=True)
        embed.add_field(name="Uso de RAM", value=f"{ram_usage:.2f} MB", inline=True)
        
        await ctx.respond(embed=embed)
        log.info(f"{ctx.author} consultó los recursos del sistema.")

    @resources.error
    async def resources_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.respond("Este comando solo puede ser usado por el propietario del bot.", ephemeral=True)

def setup(bot):
    bot.add_cog(ResourcesCog(bot))
