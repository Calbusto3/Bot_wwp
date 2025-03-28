import discord
from discord.ext import commands

class WelcomeMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_servers = {}  # Stocke les serveurs où le système est activé

        self.welcome_message_2 = """Nous vous mettons un serveur à disposition dans lequel nous **donnerons gratuitement** aux membres des jeux (**sensé être payant**) régulièrement.

- Pour y entrer, faire une **candidature** dans le serveur, soyez convaincant : 
> https://discord.gg/mwsYspWkzF 

Des questions ? -> ⁠<#1141835303573799065>"""

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Envoie le message de bienvenue uniquement si activé pour le serveur."""
        guild_id = member.guild.id

        if self.active_servers.get(guild_id, False):  # Vérifie si activé
            try:
                await member.send(self.welcome_message_2)  # Envoie le message en DM
            except discord.Forbidden:
                print(f"Impossible d'envoyer un message à {member.name} en DM.")

    @commands.command(name="a_acc")
    @commands.has_permissions(administrator=True)
    async def activate_welcome(self, ctx):
        """Active l'envoi du message en DM dans ce serveur."""
        self.active_servers[ctx.guild.id] = True
        await ctx.send("✅ Le système d'envoi du message de bienvenue en DM est **activé**.")

    @commands.command(name="d_acc")
    @commands.has_permissions(administrator=True)
    async def deactivate_welcome(self, ctx):
        """Désactive l'envoi du message en DM dans ce serveur."""
        self.active_servers[ctx.guild.id] = False
        await ctx.send("❌ Le système d'envoi du message de bienvenue en DM est **désactivé**.")

async def setup(bot):
    await bot.add_cog(WelcomeMessage(bot))
