import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from keep_alive import keep_alive

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer le token depuis la variable d'environnement
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents nécessaires
intents = discord.Intents.default()
intents.messages = True

# Création du bot avec un préfixe "!" pour les commandes
bot = commands.Bot(command_prefix="*", intents=intents)

# Événement pour quand le bot est prêt
@bot.event
async def on_ready():
    print(f'{bot.user} est connecté à Discord !')

# Démarrer le bot avec ton token sécurisé
keep_alive()
bot.run(TOKEN)
