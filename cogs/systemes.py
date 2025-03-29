import discord
import discord
from discord.ext import commands
import time
from datetime import datetime


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


    @commands.command()
    @commands.has_role(1145807576353742908)  # Vérifie si l'utilisateur a le rôle Modérateur
    async def faituntimelessde(self, ctx, duration: str):
    # Code de la commande ici...

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
            title="A ton service",
            description=f"{discord_timestamp} !",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

        # Envoi du timestamp en MP
        try:
            embed_dm = discord.Embed(
                title="Tien au cas où",
                description=f"Voici le code du timestamp que tu peux copier si jamais tu veux l'utilisez toi même, chiao :\n```\n<t:{target_time}:R>\n```",
                color=discord.Color.green()
            )
            await ctx.author.send(embed=embed_dm)
        except discord.Forbidden:
            await ctx.send("❌ Impossible d'envoyer le timestamp en MP.")

    @commands.command(name="hide")
    @commands.has_role(1145807576353742908)  # ID du rôle Modérateurs
    async def hide(self, ctx, channel: discord.TextChannel = None):
        """Cache un salon pour tout le monde sauf les modérateurs."""
        if channel is None:
            channel = ctx.channel  # Si aucun salon n'est spécifié, prend le salon actuel

        everyone_role = ctx.guild.default_role  # Récupération du rôle @everyone
        mod_role = ctx.guild.get_role(1145807576353742908)  # Rôle modérateur
        
        # On enlève la vue à @everyone
        await channel.set_permissions(everyone_role, view_channel=False)

        # On enlève la vue à tous les autres rôles sauf les modérateurs ou plus
        for role in ctx.guild.roles:
            if role.position < mod_role.position and role != everyone_role:  # On exclut les modos et plus
                await channel.set_permissions(role, view_channel=False)

        await ctx.send(f"salon {channel.mention} caché pour le moment.")

    @hide.error
    async def hide_error(self, ctx, error):
        """Gestion des erreurs"""
        if isinstance(error, commands.MissingRole):
            await ctx.send("❌ **Tu n'as pas la permission d'utiliser cette commande !**")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ **Salon introuvable !**")
        else:
            await ctx.send("❌ **Une erreur s'est produite !**")


# INFOS_AVANCEES ---------------------------------------------------------------------

    async def check_permissions(self, ctx):
        role_required = 1145807530547757107  # ID du rôle requis
        if role_required not in [role.id for role in ctx.author.roles]:
            await ctx.send("⛔ Vous n'avez pas la permission d'utiliser cette commande.")
            return False
        return True

    @commands.command(name="infos_avancé")
    async def infos_avance(self, ctx, arg1: discord.Role | discord.Member | discord.TextChannel | discord.VoiceChannel | discord.Emoji | discord.CategoryChannel, arg2: discord.Member = None):
        if not await self.check_permissions(ctx):
            return
        
        embed = discord.Embed(color=discord.Color.blue(), timestamp=datetime.utcnow())
        
        if isinstance(arg1, discord.Role):
            embed.title = f"📌 Infos sur le rôle {arg1.name}"
            embed.add_field(name="🆔 ID", value=arg1.id, inline=False)
            embed.add_field(name="📆 Créé le", value=arg1.created_at.strftime("%d/%m/%Y %H:%M"), inline=False)
            embed.add_field(name="🎨 Couleur", value=str(arg1.color), inline=False)
            embed.add_field(name="👥 Nombre de membres", value=len(arg1.members), inline=False)
            embed.set_footer(text="Infos avancées - Rôle")
        
        elif isinstance(arg1, discord.TextChannel) or isinstance(arg1, discord.VoiceChannel):
            embed.title = f"🏗️ Infos sur le salon {arg1.name}"
            embed.add_field(name="🆔 ID", value=arg1.id, inline=False)
            embed.add_field(name="📆 Créé le", value=arg1.created_at.strftime("%d/%m/%Y %H:%M"), inline=False)
            if isinstance(arg1, discord.VoiceChannel):
                embed.add_field(name="🔊 Type", value="Salon vocal", inline=False)
                active_members = arg1.members
                embed.add_field(name="👥 Membres actuellement connectés", value=len(active_members), inline=False)
            else:
                embed.add_field(name="💬 Type", value="Salon textuel", inline=False)
            embed.set_footer(text="Infos avancées - Salon")
        
        elif isinstance(arg1, discord.Member) and isinstance(arg2, discord.Role):
            if arg2 in arg1.roles:
                embed.title = f"👤 Infos sur {arg1.name} et le rôle {arg2.name}"
                embed.add_field(name="📆 Date d'attribution", value="Impossible à récupérer via l'API", inline=False)
                embed.add_field(name="🆔 ID du membre", value=arg1.id, inline=False)
            else:
                embed.title = "❌ Aucune relation trouvée"
                embed.description = f"{arg1.name} ne possède pas le rôle {arg2.name}."
            embed.set_footer(text="Infos avancées - Membre & Rôle")
        
        elif isinstance(arg1, discord.Emoji):
            embed.title = f"😀 Infos sur l'emoji {arg1.name}"
            embed.add_field(name="🆔 ID", value=arg1.id, inline=False)
            embed.add_field(name="📆 Ajouté le", value=arg1.created_at.strftime("%d/%m/%Y %H:%M"), inline=False)
            embed.set_footer(text="Infos avancées - Emoji")
        
        elif isinstance(arg1, discord.CategoryChannel):
            embed.title = f"📂 Infos sur la catégorie {arg1.name}"
            embed.add_field(name="🆔 ID", value=arg1.id, inline=False)
            embed.add_field(name="📆 Créée le", value=arg1.created_at.strftime("%d/%m/%Y %H:%M"), inline=False)
            embed.add_field(name="📜 Nombre de salons", value=len(arg1.channels), inline=False)
            embed.set_footer(text="Infos avancées - Catégorie")
        
        else:
            embed.title = "❌ Erreur"
            embed.description = "Mauvais paramètres ou données introuvables."
            embed.set_footer(text="Infos avancées - Erreur")
        
        await ctx.send(embed=embed)    
async def setup(bot):
    await bot.add_cog(WelcomeMessage(bot))
