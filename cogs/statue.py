import discord
from discord.ext import commands

class Statut(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Définir l'activité par défaut
        activity = discord.Activity(type=discord.ActivityType.watching, name="War wor Porn")
        await self.bot.change_presence(activity=activity)
        print(f"{self.bot.user} est prêt")

    # REGARDE
    @commands.command(name="set_watch_status", help="Change l'activité du bot en 'regarde'.")
    @commands.has_permissions(administrator=True)
    async def set_watch_status(self, ctx: commands.Context, *, statut: str):
        if len(statut) > 128:
            await ctx.send("Le statut est trop long (max 128 caractères).")
            return
        activity = discord.Activity(type=discord.ActivityType.watching, name=statut)
        await self.bot.change_presence(activity=activity)
        await ctx.send(f"Le bot regarde désormais : '{statut}'")

    # JEU
    @commands.command(name="set_play_status", help="Change l'activité du bot en 'joue à'.")
    @commands.has_permissions(administrator=True)
    async def set_play_status(self, ctx: commands.Context, *, statut: str):
        if len(statut) > 128:
            await ctx.send("Le statut est trop long (max 128 caractères).")
            return
        activity = discord.Activity(type=discord.ActivityType.playing, name=statut)
        await self.bot.change_presence(activity=activity)
        await ctx.send(f"Le bot joue désormais à '{statut}'.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Statut(bot))