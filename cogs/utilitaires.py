import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

class Utilitaire(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="fake", description="Affiche un membre comme fake")
    @app_commands.describe(member="Le membre à afficher comme fake")
    async def fake(self, interaction: discord.Interaction, member: discord.Member):
        """Marque un utilisateur comme fake en ajoutant '[fake]' à son pseudo."""
        # Nouveau pseudo
        new_nick = f"[fake] {member.display_name}"

        # Vérifie les permissions du bot
        if not interaction.guild.me.guild_permissions.manage_nicknames:
            await interaction.response.send_message(
                "Je n'ai pas la permission de changer les pseudos des membres.", ephemeral=True
            )
            return

        try:
            # Applique le pseudo
            await member.edit(nick=new_nick)
            await interaction.response.send_message(
                f"{member.mention} a été affiché comme fake.", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                f"Je n'ai pas les permissions nécessaires pour modifier le pseudo de {member.mention}.", 
                ephemeral=True
            )
            return
        except Exception as e:
            await interaction.response.send_message(
                f"Erreur inattendue : {str(e)}", ephemeral=True
            )
            return

        # Notification dans le canal défini
        salon_id = 1250466390675292201
        channel = self.bot.get_channel(salon_id)
        if channel:
            await channel.send(
                f"{member.mention} est considéré comme fake par le staff, attention aux interactions avec cette personne."
            )
        else:
            await interaction.followup.send("Le salon d'annonce n'a pas été trouvé.", ephemeral=True)

    @app_commands.command(name="unfake", description="Retire le statut de fake d'un membre")
    @app_commands.describe(member="Le membre dont on veut retirer le statut de fake")
    async def unfake(self, interaction: discord.Interaction, member: discord.Member):
        """Retire le statut de fake en enlevant le préfixe '[fake]' du pseudo d'un membre."""
        
        # Si le pseudo contient [fake], on l'enlève
        if member.display_name.startswith("[fake]"):
            new_nick = member.display_name[7:]  # Enlève le préfixe "[fake] "
        else:
            await interaction.response.send_message(
                f"{member.mention} n'est pas afficher comme 'fake'.", ephemeral=True
            )
            return

        # Vérifie les permissions du bot
        if not interaction.guild.me.guild_permissions.manage_nicknames:
            await interaction.response.send_message(
                "Je n'ai pas la permission de changer les pseudos des membres.", ephemeral=True
            )
            return

        try:
            # Applique le nouveau pseudo
            await member.edit(nick=new_nick)
            await interaction.response.send_message(
                f"Le statut de fake de {member.mention} a été retiré.", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                f"Je n'ai pas les permissions nécessaires pour enlever {member.mention} comme fake.", 
                ephemeral=True
            )
            return
        except Exception as e:
            await interaction.response.send_message(
                f"Erreur inattendue : {str(e)}", ephemeral=True
            )
            return

        # Notification dans le canal défini
        salon_id = 1250466390675292201
        channel = self.bot.get_channel(salon_id)
        if channel:
            await channel.send(
                f"{member.mention} n'est plus considéré comme fake par le staff."
            )
        else:
            await interaction.followup.send("Le salon d'annonce n'a pas été trouvé.", ephemeral=True)

# supp

    @commands.hybrid_command(name="supprime", aliases=["sup"], with_app_command=True)
    @commands.has_permissions(manage_messages=True)
    async def supprimer(self, ctx: commands.Context, nombre: int):
        await ctx.message.delete()  # Supprime le message de commande immédiatement.

        if nombre < 1:
            await ctx.send("Vous devez indiquer un nombre valide supérieur à 0.", delete_after=5)
            return

        deleted = await ctx.channel.purge(limit=nombre)
        
        # Message de confirmation.
        confirmation = await ctx.send(f"🗑️ {len(deleted)} message(s) supprimé(s).")
        await confirmation.delete(delay=5)
        
    @discord.app_commands.command(name="envoie", description="Envoyer un message sous l'identité su bot.")
    async def say_slash(self, interaction: discord.Interaction, message: str):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Vous n'avez pas la permission pour cette commande.", ephemeral=True)
            return
        await interaction.channel.send(message)
        await interaction.response.send_message("✅ Message envoyé avec succès !", ephemeral=True)

    # Commande préfixe +say
    @commands.command(name="envoie")
    @commands.has_permissions(manage_channels=True)
    async def say_prefix(self, ctx, *, message: str):
        await ctx.channel.send(message)
        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass
        
    # mute
    @commands.hybrid_command(name="muter", description="Mute un membre pendant une durée spécifiée.")
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: int, reason: str = None):
        """Mute un membre pour une durée spécifiée."""
        if not ctx.author.guild_permissions.mute_members:
            await ctx.send("❌ Vous n'avez pas la permission pour cette commande.", ephemeral=True)
            return

        # Calcul de la durée de mute en secondes
        mute_duration = timedelta(minutes=duration)
        
        try:
            # Application du mute
            await member.timeout(mute_duration, reason=reason)
            await ctx.send(f"{member} a été mute pour {duration} minutes. Raison: {reason if reason else 'Aucune'}.")
        except Exception as e:
            await ctx.send(f"❌ Une erreur s'est produite : {str(e)}")

    # unmute
    @commands.hybrid_command(name="unmuter", description="Unmute un membre.")
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        """Unmute un membre pour lui permettre de parler à nouveau."""
        if not ctx.author.guild_permissions.mute_members:
            await ctx.send("❌ Vous n'avez pas la permission pour cette commande.", ephemeral=True)
            return

        try:
            # Annulation du mute
            await member.timeout(None)
            await ctx.send(f"{member} a été unmute.")
        except Exception as e:
            await ctx.send(f"❌ Une erreur s'est produite : {str(e)}")

    # ban
    @commands.hybrid_command(name="bannir", description="Bannir un membre du serveur.")
    async def ban(self, ctx: commands.Context, member: discord.Member = None, reason: str = None):
        # Vérification des permissions
        if not ctx.author.guild_permissions.ban_members:
            await ctx.send("❌ Vous n'avez pas la permission de bannir les membres.")
            return

        # Si aucun membre n'est mentionné, renvoyer un message d'erreur
        if member is None:
            await ctx.send("❌ Veuillez mentionner un membre à bannir.")
            return

        # Tentative de bannir le membre
        try:
            # Bannir le membre avec une raison
            await member.ban(reason=reason)
            
            # Création du message Embed
            embed = discord.Embed(
                title="Vous avez été banni du serveur",
                description=f"Vous avez été banni du serveur pour la raison suivante : {reason if reason else 'Aucune raison spécifiée.'}",
                color=discord.Color.red()
            )
            embed.set_footer(text="Pour contester ce ban, veuillez passer par ce formulaire.")
            embed.add_field(name="Formulaire de contestation", value="[Cliquez ici pour contester le ban](https://forms.gle/RKeGRaaBsrYHQXAp6)", inline=False)

            # Envoi de l'embed en DM au membre banni
            await member.send(embed=embed)

            # Message de confirmation dans le serveur
            await ctx.send(f"{member} a été banni avec succès pour la raison : {reason if reason else 'Aucune.'}")
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission de bannir ce membre.")
        except discord.HTTPException:
            await ctx.send("❌ Une erreur s'est produite en tentant de bannir ce membre.")

    # unban
    @commands.hybrid_command(name="unbannir", description="Unbannir un membre du serveur.")
    async def unban(self, ctx: commands.Context, user_id: int, reason: str = None):
        # Vérification des permissions
        if not ctx.author.guild_permissions.ban_members:
            await ctx.send("❌ Vous n'avez pas la permission de unban les membres.")
            return

        # Tentative de unban
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=reason)
            await ctx.send(f"{user} a été débanni avec succès.")
        except discord.NotFound:
            await ctx.send("❌ Aucun membre correspondant à cet ID n'a été trouvé.")
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas les permissions nécessaires pour effectuer cette action.")
  
async def setup(bot: commands.Bot):
    await bot.add_cog(Utilitaire(bot))