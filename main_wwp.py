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
            cog_name = f"cogs.{filename[:-3]}"  # Enlever le ".py" du nom de fichier
            bot.loop.create_task(load_cog(cog_name))

    # Synchronisation des commandes slash (app_commands)
    try:
        await bot.tree.sync()  # Synchronise toutes les commandes slash du bot
        print("Commandes slash synchronisées.")
    except Exception as e:
        print(f"Erreur lors de la synchronisation des commandes slash : {e}")

    # Définir l'activité du bot
    activity = discord.Activity(type=discord.ActivityType.watching, name="World War Porn")
    await bot.change_presence(activity=activity)

# Fonction asynchrone pour charger les cogs
async def load_cog(cog_name):
    try:
        await bot.load_extension(cog_name)
        print(f"Cog {cog_name} chargé avec succès.")
    except Exception as e:
        print(f"Erreur lors du chargement de {cog_name}: {e}")

# Démarrer le bot avec ton token sécurisé
keep_alive()
bot.run(TOKEN)
