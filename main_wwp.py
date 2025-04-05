# Code principal du bot
import discord
from discord.ext import commands
from discord import app_commands
import os
from keep_alive import keep_alive

# Charger les variables d'environnement depuis le fichier .env
from dotenv import load_dotenv
load_dotenv()

# Récupérer le token depuis la variable d'environnement
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents nécessaires
intents = discord.Intents.all()

# Création du bot avec un préfixe "+" pour les commandes et support des commandes slash
bot = commands.Bot(command_prefix="+", intents=intents, help_command=None)

# Charger les cogs automatiquement
@bot.event
async def on_ready():
    print(f'{bot.user} est connecté à Discord !')

    # Charger les cogs
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            cog_name = f"cogs.{filename[:-3]}"
            await bot.load_extension(cog_name)  # Charger chaque cog
            print(f"Cog {filename} chargé avec succès.")

    # Synchronisation des commandes slash
    await bot.tree.sync()  # Synchronise toutes les commandes slash du bot
    print("Commandes slash synchronisées.")

# Commande pour recharger un cog
@commands.command(name="reload")
@commands.is_owner()
async def reload(ctx, extension: str):
    try:
        await ctx.bot.reload_extension(f"cogs.{extension}")
        await ctx.send(f"✅ Cog `{extension}` rechargé avec succès.")
    except Exception as e:
        await ctx.send(f"❌ Erreur lors du rechargement du cog `{extension}` : {e}")

# Démarrer le bot avec ton token sécurisé
keep_alive()
bot.run(TOKEN)