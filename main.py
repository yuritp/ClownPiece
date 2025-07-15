import discord
import os
from dotenv import load_dotenv # <--- AÑADIDO

# Carga las variables del archivo .env en el entorno del sistema
load_dotenv() # <--- AÑADIDO

# Ahora obtenemos el token desde las variables de entorno
TOKEN = os.getenv("DISCORD_TOKEN") # <--- CAMBIADO

# Definimos los intents que nuestro bot necesita
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

# Inicializamos el bot
bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print("="*30)
    print(f'✅ {bot.user} se ha conectado a Discord!')
    print("="*30)

# Bucle para cargar las extensiones (Cogs)
for filename in os.listdir('./cogs'):
    if filename.endswith('.py') and filename != '__init__.py':
        try:
            bot.load_extension(f'cogs.{filename[:-3]}')
            print(f"-> Cog '{filename[:-3]}' cargado exitosamente.")
        except Exception as e:
            print(f"🚨 Error al cargar el cog '{filename[:-3]}': {e}")


# Ejecuta el bot con el token cargado desde el .env
if __name__ == "__main__":
    if not TOKEN: # <--- CAMBIADO para comprobar si el token se cargó
         print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
         print("!!!   ERROR: DISCORD_TOKEN no encontrado en el archivo .env   !!!")
         print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        bot.run(TOKEN)