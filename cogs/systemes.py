import discord
import discord
from discord.ext import commands
import time


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


    @commands.command(name="faituntimelessde")
    async def faituntimelessde(self, ctx, duration: str):
        """Génère un timestamp Discord et l'affiche en embed + DM au membre."""
        unit_mapping = {"s": 1, "m": 60, "h": 3600, "j": 86400}

        # Vérification de l'entrée utilisateur
        try:
            value, unit = int(duration[:-1]), duration[-1].lower()
            if unit not in unit_mapping:
                raise ValueError
        except ValueError:
            await ctx.send("⚠️ **Format invalide !** Utilise : `+faituntimelessde [nombre][s/m/h/j]`")
            return

        # Calcul du timestamp
        current_time = int(time.time())
        target_time = current_time + (value * unit_mapping[unit])

        # Formatage du timestamp pour Discord
        discord_timestamp = f"<t:{target_time}:R>"

        # Envoi du message dans le salon
        embed = discord.Embed(
            title="ok",
            description=f"{discord_timestamp} !",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

        # Envoi du timestamp en MP
        try:
            embed_dm = discord.Embed(
                title="Tien au cas où",
                description=f"Voici le code du timestamp que vous pouvez copier :\n```\n<t:{target_time}:R>\n```",
                color=discord.Color.green()
            )
            await ctx.author.send(embed=embed_dm)
        except discord.Forbidden:
            await ctx.send("❌ Impossible d'envoyer le timestamp en MP.")

async def setup(bot):
    await bot.add_cog(WelcomeMessage(bot))
