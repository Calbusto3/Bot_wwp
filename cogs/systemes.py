import discord
from discord.ext import commands
from datetime import datetime
import json
import time

class ServerBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hidden_channels = {} 
        self.active_servers = {}  # Stocke les serveurs où le système est activé
        self.logs = {}
        self.welcome_message_2 = """Bienvenue chez nous !

Nous mettons à votre disposition un serveur où nous **offrons gratuitement** des jeux qui sont normalement payants.

- Pour y accéder, n'oubliez pas de faire une **candidature** sérieuse : 
> https://discord.gg/mwsYspWkzF 

Si tu as des questions, n’hésite pas à nous rejoindre dans ⁠<#1141835303573799065>."""

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = member.guild.id
        if self.active_servers.get(guild_id, False):
            try:
                await member.send(self.welcome_message_2)
            except discord.Forbidden:
                print(f"Impossible d'envoyer un message à {member.name} en DM.")

    @commands.command(name="a_acc")
    @commands.has_permissions(manage_guild=True)
    async def activate_welcome(self, ctx):
        self.active_servers[ctx.guild.id] = True
        await ctx.send("✅ Message de bienvenue en DM **activé** !")

    @commands.command(name="d_acc")
    @commands.has_permissions(manage_guild=True)
    async def deactivate_welcome(self, ctx):
        self.active_servers[ctx.guild.id] = False
        await ctx.send("❌ Message de bienvenue en DM **désactivé**.")

    @commands.command(name="hide")
    @commands.has_permissions(manage_guild=True)
    async def hide(self, ctx, channel: discord.TextChannel = None):
        """Cache un salon pour tout le monde sauf les modérateurs."""
        if channel is None:
            channel = ctx.channel  # Par défaut, cache le salon actuel

        everyone_role = ctx.guild.default_role  # Rôle @everyone
        mod_role = ctx.guild.get_role(1145807576353742908)  # Rôle modérateur

        # Sauvegarde des permissions avant modification
        if channel.id not in self.hidden_channels:
            self.hidden_channels[channel.id] = {
                role.id: channel.overwrites.get(role) for role in ctx.guild.roles if role.position < mod_role.position
            }

        # Appliquer les restrictions
        await channel.set_permissions(everyone_role, view_channel=False)
        for role in ctx.guild.roles:
            if role.position < mod_role.position and role != everyone_role:
                await channel.set_permissions(role, view_channel=False)

        await ctx.send(f"le salon {channel.mention} est maintenant caché.")

    @commands.command(name="unhide")
    @commands.has_permissions(manage_guild=True)
    async def unhide(self, ctx, channel: discord.TextChannel = None):
        """Rend un salon visible à nouveau en restaurant les permissions initiales."""
        if channel is None:
            channel = ctx.channel  # Par défaut, restaure le salon actuel

        if channel.id not in self.hidden_channels:
            await ctx.send("déjà visible par tous")
            return

        # Restauration des permissions originales
        for role_id, overwrite in self.hidden_channels[channel.id].items():
            role = ctx.guild.get_role(role_id)
            if role:
                await channel.set_permissions(role, overwrite=overwrite)

        del self.hidden_channels[channel.id]  # Supprime les données sauvegardées

        await ctx.send(f"tout le monde peut à nouveau voir {channel.mention}.")

    @hide.error
    async def hide_error(self, ctx, error):
        """Gestion des erreurs de la commande hide"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ **Tu n'as pas la permission pour cette commande**")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ **Salon introuvable**")
        else:
            await ctx.send("❌ **Oups, une erreur est survenue**")

    async def log_event(self, event_type, user, target, details):
        event_data = {
            "event_type": event_type,
            "user": user.name,
            "user_id": user.id,
            "target": target.name if isinstance(target, discord.Member) else target.id,
            "target_id": target.id if isinstance(target, discord.Member) else None,
            "details": details,
            "timestamp": datetime.utcnow().strftime("%d/%m/%Y %H:%M")
        }
        if target.id not in self.logs:
            self.logs[target.id] = []
        self.logs[target.id].append(event_data)
        with open('event_logs.json', 'w') as f:
            json.dump(self.logs, f, indent=4)

    @commands.command(name="infos_avancé")
    @commands.has_permissions(manage_guild=True)
    async def infos_avance(self, ctx, arg1: discord.Role | discord.Member | discord.TextChannel | discord.VoiceChannel | discord.Emoji | discord.CategoryChannel, arg2: discord.Member = None):
        if not await self.check_permissions(ctx):
            return
        
        embed = discord.Embed(color=discord.Color.blue(), timestamp=datetime.utcnow())
        logs_data = self.logs.get(arg1.id if isinstance(arg1, (discord.Member, discord.Role, discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel)) else None, [])
        
        if isinstance(arg1, discord.Role):
            embed.title = f"📌 Infos sur le rôle {arg1.name}"
            embed.add_field(name="🆔 ID", value=arg1.id, inline=False)
            embed.add_field(name="📆 Créé le", value=arg1.created_at.strftime("%d/%m/%Y %H:%M"), inline=False)
            embed.add_field(name="🎨 Couleur", value=str(arg1.color), inline=False)
            embed.add_field(name="👥 Nombre de membres", value=len(arg1.members), inline=False)
            
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
                embed.add_field(name="👥 Membres actuellement connectés", value=len(arg1.members), inline=False)
            else:
                embed.add_field(name="💬 Type", value="Salon textuel", inline=False)
            
            channel_logs = "\n".join([f"{log['timestamp']} - {log['user']} ({log['user_id']}) - {log['details']}" for log in logs_data])
            if channel_logs:
                embed.add_field(name="🔖 Logs", value=channel_logs, inline=False)
            
            embed.set_footer(text="Infos avancées - Salon")
        
        await ctx.send(embed=embed)

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
            await ctx.send("**Format invalide !** Utilise : `+faituntimelessde [nombre][s/m/h/j]`")
            return

        # Calcul du timestamp
        current_time = int(time.time())
        target_time = current_time + (value * unit_mapping[unit])

        # Formatage du timestamp pour Discord
        discord_timestamp = f"<t:{target_time}:R>"

        # Envoi du message dans le salon
        embed = discord.Embed(
            title="à ton service",
            description=f"{discord_timestamp}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

        # Envoi du timestamp en MP
        try:
            embed_dm = discord.Embed(
                title="Regarde",
                description=f"si tu veux utiliser le timetamp que t'as généré, utilise ce code :\n```\n<t:{target_time}:R>\n```",
                color=discord.Color.green()
            )
            await ctx.author.send(embed=embed_dm)
        except discord.Forbidden:
            await ctx.send("impossible d'envoyer le timestamp en MP.")

async def setup(bot):
    await bot.add_cog(ServerBot(bot))
