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
intents = discord.Intents.all()

# Création du bot avec un préfixe "*" pour les commandes et support des commandes slash
bot = commands.Bot(command_prefix="*", intents=intents, help_command=None)

# Charger les cogs automatiquement
@bot.event
async def on_ready():
    print(f'{bot.user} est connecté à Discord !')

    # Parcourir le dossier "cogs" et charger chaque fichier python qui est un cog
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            # Charger l'extension (le cog)
            cog_name = f"cogs.{filename[:-3]}"  # Enlever le ".py" du nom de fichier
            bot.load_extension(cog_name)
            print(f"Cog {filename} chargé avec succès.")

    # Synchronisation des commandes slash (app_commands)
    await bot.tree.sync()  # Synchronise toutes les commandes slash du bot

# Démarrer le bot avec ton token sécurisé
keep_alive()
bot.run(TOKEN)