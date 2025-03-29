import discord
from discord.ext import commands
from datetime import datetime
import json

class ServerBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_servers = {}  # Stocke les serveurs où le système est activé
        self.logs = {}
        self.welcome_message_2 = """Bienvenue chez nous !

Nous mettons à votre disposition un serveur où nous **offrons gratuitement** des jeux qui sont normalement payants.

- Pour y accéder, n'oubliez pas de faire une **candidature** sérieuse : 
> https://discord.gg/mwsYspWkzF 

Si tu as des questions, n’hésite pas à nous rejoindre dans ⁠<#1141835303573799065>."""

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
        """Active l'envoi du message de bienvenue en DM pour ce serveur."""
        self.active_servers[ctx.guild.id] = True
        await ctx.send("✅ Message de bienvenue en DM **activé** !")

    @commands.command(name="d_acc")
    @commands.has_permissions(administrator=True)
    async def deactivate_welcome(self, ctx):
        """Désactive l'envoi du message de bienvenue en DM pour ce serveur."""
        self.active_servers[ctx.guild.id] = False
        await ctx.send("❌ Message de bienvenue en DM **désactivé**.")

    @commands.command(name="hide")
    @commands.has_role(1145807576353742908)  # ID du rôle Modérateur
    async def hide(self, ctx, channel: discord.TextChannel = None):
        """Cache un salon pour tout le monde sauf les modérateurs."""
        if channel is None:
            channel = ctx.channel  # Si aucun salon n'est spécifié, prend le salon actuel

        everyone_role = ctx.guild.default_role  # Récupération du rôle @everyone
        mod_role = ctx.guild.get_role(1145807576353742908)  # Rôle modérateur
        
        # Cache le salon pour @everyone
        await channel.set_permissions(everyone_role, view_channel=False)

        # Cache le salon pour tous les autres rôles sauf les modérateurs ou rôles supérieurs
        for role in ctx.guild.roles:
            if role.position < mod_role.position and role != everyone_role:
                await channel.set_permissions(role, view_channel=False)

        await ctx.send(f"Le salon {channel.mention} est maintenant caché.")

    @hide.error
    async def hide_error(self, ctx, error):
        """Gestion des erreurs de la commande hide"""
        if isinstance(error, commands.MissingRole):
            await ctx.send("❌ **Tu n'as pas la permission pour cette commande !**")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ **Salon introuvable !**")
        else:
            await ctx.send("❌ **Oups, quelque chose ne va pas**")

    async def check_permissions(self, ctx):
        role_required = 1145807530547757107  # ID du rôle requis
        if role_required not in [role.id for role in ctx.author.roles]:
            await ctx.send("⛔ Tu n'as pas les autorisations nécessaires pour cette commande.")
            return False
        return True

    async def log_event(self, event_type, user, target, details):
        """Enregistre les événements (ex: attribution de rôle, création de salon, etc.)"""
        event_data = {
            "event_type": event_type,
            "user": user.name,
            "user_id": user.id,
            "target": target.name if isinstance(target, discord.Member) else target.id,
            "target_id": target.id if isinstance(target, discord.Member) else None,
            "details": details,
            "timestamp": datetime.utcnow().strftime("%d/%m/%Y %H:%M")
        }
        # Enregistrer dans un fichier JSON pour les logs
        if target.id not in self.logs:
            self.logs[target.id] = []
        self.logs[target.id].append(event_data)
        
        # Écriture dans le fichier JSON
        with open('event_logs.json', 'w') as f:
            json.dump(self.logs, f, indent=4)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Surveille les changements sur un membre, comme un rôle ajouté/supprimé."""
        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            
            for role in added_roles:
                # Log l'attribution du rôle
                await self.log_event("Role Assigned", after, role, f"Rôle {role.name} attribué.")
            for role in removed_roles:
                # Log la suppression du rôle
                await self.log_event("Role Removed", after, role, f"Rôle {role.name} supprimé.")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Log de la création de salons."""
        if isinstance(channel, discord.TextChannel):
            await self.log_event("Channel Created", channel.guild.owner, channel, f"Salon textuel {channel.name} créé.")
        elif isinstance(channel, discord.VoiceChannel):
            await self.log_event("Channel Created", channel.guild.owner, channel, f"Salon vocal {channel.name} créé.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Log de l'entrée d'un membre."""
        await self.log_event("Member Joined", member, member.guild, "Membre a rejoint le serveur.")

    @commands.command(name="infos_avancé")
    async def infos_avance(self, ctx, arg1: discord.Role | discord.Member | discord.TextChannel | discord.VoiceChannel | discord.Emoji | discord.CategoryChannel, arg2: discord.Member = None):
        if not await self.check_permissions(ctx):
            return
        
        embed = discord.Embed(color=discord.Color.blue(), timestamp=datetime.utcnow())

        # Récupération des logs pour l'argument donné
        logs_data = self.logs.get(arg1.id if isinstance(arg1, (discord.Member, discord.Role, discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel)) else None, [])
        
        if isinstance(arg1, discord.Role):
            embed.title = f"📌 Infos sur le rôle {arg1.name}"
            embed.add_field(name="🆔 ID", value=arg1.id, inline=False)
            embed.add_field(name="📆 Créé le", value=arg1.created_at.strftime("%d/%m/%Y %H:%M"), inline=False)
            embed.add_field(name="🎨 Couleur", value=str(arg1.color), inline=False)
            embed.add_field(name="👥 Nombre de membres", value=len(arg1.members), inline=False)

            # Ajout des logs associés au rôle
            role_logs = "\n".join([f"{log['timestamp']} - {log['user']} ({log['user_id']}) - {log['details']}" for log in logs_data])
            if role_logs:
                embed.add_field(name="🔖 Logs", value=role_logs, inline=False)
            
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

            # Ajout des logs associés au salon
            channel_logs = "\n".join([f"{log['timestamp']} - {log['user']} ({log['user_id']}) - {log['details']}" for log in logs_data])
            if channel_logs:
                embed.add_field(name="🔖 Logs", value=channel_logs, inline=False)

            embed.set_footer(text="Infos avancées - Salon")

        elif isinstance(arg1, discord.Member) and isinstance(arg2, discord.Role):
            if arg2 in arg1.roles:
                embed.title = f"👤 Infos sur {arg1.name} et le rôle {arg2.name}"
                embed.add_field(name="📆 Date d'attribution", value="Impossible à récupérer via l'API", inline=False)
                embed.add_field(name="🆔 ID du membre", value=arg1.id, inline=False)
                
                # Ajout des logs associés au membre et au rôle
                member_role_logs = "\n".join([f"{log['timestamp']} - {log['user']} ({log['user_id']}) - {log['details']}" for log in logs_data])
                if member_role_logs:
                    embed.add_field(name="🔖 Logs", value=member_role_logs, inline=False)
            
            else:
                embed.title = "❌ Aucune relation trouvée"
                embed.description = f"{arg1.name} ne possède pas le rôle {arg2.name}."
            embed.set_footer(text="Infos avancées - Membre & Rôle")

        else:
            embed.title = "❌ Erreur"
            embed.description = "Mauvais paramètres ou données introuvables."
            embed.set_footer(text="Infos avancées - Erreur")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerBot(bot))