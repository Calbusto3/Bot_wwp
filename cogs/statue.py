import discord
from discord.ext import commands

class Statut(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Définir l'activité du bot à "Regarde la télé"
        activity = discord.Activity(type=discord.ActivityType.watching, name="Pornhub")
        await self.bot.change_presence(activity=activity)
        print(f"{self.bot.user} a démarré et regarde la télé !")

    @commands.command()
    async def changer_statu(self, ctx, *, statut: str):
        """Permet de changer l'activité du bot."""
        activity = discord.Activity(type=discord.ActivityType.watching, name=statut)
        await self.bot.change_presence(activity=activity)
        await ctx.send(f"Le bot regarde désormais : {statut}")

# Ajouter le cog
def setup(bot):
    bot.add_cog(Statut(bot))