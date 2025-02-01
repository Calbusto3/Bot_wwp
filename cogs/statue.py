import discord
from discord.ext import commands
from discord import app_commands

class Statut(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Définir l'activité du bot à "World War P'"
        activity = discord.Activity(type=discord.ActivityType.watching, name="World War P'")
        await self.bot.change_presence(activity=activity)
        print(f"{self.bot.user} a démarré et regarde la télé !")

    @commands.hybrid_command(name="changer_statu", description="Change l'activité du bot.")
    @commands.has_permissions(administrator=True)
    async def changer_statu(self, ctx: commands.Context, *, statut: str):
        """Permet de changer l'activité du bot."""
        activity = discord.Activity(type=discord.ActivityType.watching, name=statut)
        await self.bot.change_presence(activity=activity)
        await ctx.send(f"Le bot regarde désormais : {statut}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Statut(bot))