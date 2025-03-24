from typing import Optional
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
import random
from discord import app_commands, Embed, Forbidden, Member
from discord.ui import View, Select
import string


class Utilitaire(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Liste des rôles selon le genre
        self.roles_homme = [1248044201959227414, 1248282343718780979]  # Remplace par tes IDs de rôles homme
        self.roles_femme = [1248044201959227414, 1248282244779343992]  # Remplace par tes IDs de rôles femme

        # ID du salon pour annoncer la vérification
        self.salon_annonce_id = 1353301864049016833  # Remplace par l'ID du salon d'annonce
        self.salon_archive_id = 1353299043261874230  # Remplace par l'ID du salon d'archives

        # Stockage des codes pour éviter les doublons (en mémoire, à mettre en BDD si besoin)
        self.generated_codes = set()

    @commands.hybrid_command(name="vérifier", description="Vérifier un membre.")
    @commands.has_permissions(manage_roles=True)  # Permission correcte ici
    async def verifier(self, ctx: commands.Context, membre: discord.Member):

            # Création du select pour choisir homme/femme
            options = [
                discord.SelectOption(label="Homme", description="Vérifier comme homme", value="homme"),
                discord.SelectOption(label="Femme", description="Vérifier comme femme", value="femme")
            ]

            select = Select(placeholder="Choisissez le genre", options=options)

            async def select_callback(interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("Seul l'auteur de la commande peut faire cette sélection.", ephemeral=True)
                    return

                genre = select.values[0]

                # Attribution des rôles
                if genre == "homme":
                    for role_id in self.roles_homme:
                        role = ctx.guild.get_role(role_id)
                        if role:
                            await membre.add_roles(role)
                else:
                    for role_id in self.roles_femme:
                        role = ctx.guild.get_role(role_id)
                        if role:
                            await membre.add_roles(role)

                # Message d'annonce dans le salon
                salon_annonce = ctx.guild.get_channel(self.salon_annonce_id)
                if salon_annonce:
                    await salon_annonce.send(f"{membre.mention} a été vérifié en tant que **{genre}** ! Vous ne risquez plus de vous faire arnaquer par cette personne")

                # Génération d'un code unique
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                while code in self.generated_codes:
                    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                self.generated_codes.add(code)

                # MP au membre (embed)
                try:
                    embed_dm = discord.Embed(
                        title="Vérification réussie !",
                        description=f"Félicitations {membre.mention}, vous êtes maintenant vérifié(e) sur **{ctx.guild.name}** !",
                        color=discord.Color.green()
                    )
                    embed_dm.add_field(name="📄 Code de vérification", value=f"`{code}`", inline=False)
                    embed_dm.set_footer(text="Conservez bien ce code.")
                    embed_dm.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else discord.Embed.Empty)

                    await membre.send(embed=embed_dm)

                except discord.Forbidden:
                    await interaction.followup.send("Je n'ai pas pu envoyer un MP au membre. Il/elle ne recevra pas son code de vérification.", ephemeral=True)

                # Archivage du code
                salon_archive = ctx.guild.get_channel(self.salon_archive_id)
                if salon_archive:
                    date = discord.utils.format_dt(discord.utils.utcnow(), "D")
                    await salon_archive.send(f"🔒 {membre} vérifié le {date} | Code de vérification : `{code}`")

                await interaction.response.send_message(f"{membre.mention} est maintenant vérifié(e) !", ephemeral=True)

            select.callback = select_callback
            view = View()
            view.add_item(select)

            await ctx.send("Sélectionnez le genre :", view=view)

    @app_commands.command(name="fake", description="Affiche un membre comme fake")
    @app_commands.describe(
        member="Le membre à afficher comme fake", 
        avertir="Voulez-vous avertir le membre ?",
        preuve="Ajoutez une image comme preuve (facultatif)"
    )
    async def fake(self, interaction: discord.Interaction, member: discord.Member, avertir: bool = False, preuve: Optional[discord.Attachment] = None):
        """Marque un utilisateur comme fake en ajoutant '[fake]' à son pseudo."""

        new_nick = f"[FAKE] {member.display_name}"

        # Essayer de modifier le pseudo du membre
        try:
            await member.edit(nick=new_nick)
            await interaction.response.send_message(
                f"{member.mention} a été affiché comme fake."
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                f"Je n'ai pas les permissions nécessaires pour afficher {member.mention} comme fake.",
                ephemeral=True
            )
            return

        salon_id = 1250466390675292201
        channel = self.bot.get_channel(salon_id)

        # Essayer d'envoyer un message dans le salon d'annonce
        try:
            if channel:
                message = f"{member.mention} est considéré comme fake par le staff, attention aux interactions avec cette personne."
                if preuve:
                    # Préparer le fichier si une preuve est fournie
                    file = await preuve.to_file()
                    await channel.send(message, file=file)
                else:
                    await channel.send(message)
            else:
                await interaction.followup.send("Le salon d'annonce n'a pas été trouvé.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Erreur lors de l'envoi du message d'annonce : {str(e)}", ephemeral=True)

        # Avertir le membre si l'option est activée
        if avertir:
            embed = discord.Embed(
                title="Vous êtes marqué comme fake",
                description=(f"Bonjour {member.mention},\n\n"
                             "Vous avez été marqué comme `fake` par le staff. "
                             "Si vous pensez que cette décision est une erreur, vous pouvez ouvrir un ticket "
                             "pour vous faire vérifier et retirer cette mention.\n\n"
                             "Merci de votre compréhension - World War Porn."),
                color=discord.Color.red()
            )
            embed.set_footer(text="Contactez le staff via un ticket si besoin.")
            
            # Essayer d'envoyer un message privé au membre
            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                await interaction.followup.send(
                    f"Impossible d'avertir {member.mention} par message privé, il doit les avoir désactivé."
                )

    @app_commands.command(name="unfake", description="Retire le statut de fake d'un membre")
    @app_commands.describe(member="Le membre dont on veut retirer le statut de fake")
    async def unfake(self, interaction: discord.Interaction, member: discord.Member):
        """Retire le statut de fake en enlevant le préfixe '[fake]' du pseudo d'un membre."""
        
        # Si le pseudo contient [fake], on l'enlève
        if member.display_name.startswith("[FAKE]"):
            new_nick = member.display_name[7:]  # Enlève le préfixe "[fake] "
        else:
            await interaction.response.send_message(
                f"{member.mention} n'est pas affiché comme 'fake'.", ephemeral=True
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
                f"Le statut de fake de {member.mention} a été retiré."
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
        
    @app_commands.command(name="envoie", description="Envoyer un message sous l'identité du bot.")
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

    @commands.hybrid_command(name="ban", description="Bannit un membre du serveur.")
    @app_commands.describe(
        membre="Le membre à bannir (mention ou ID)",
        raison="La raison du ban"
    )
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, membre: Member, raison: str = "Aucune raison spécifiée"):
        """Commande pour bannir un membre avec confirmation et GIF aléatoire."""

        # Embed pour MP du membre banni
        dm_embed = Embed(
            title="🚫 Tu as été banni !",
            description=f"**Serveur :** {ctx.guild.name}\n**Raison :** {raison}",
            color=discord.Color.red()
        )
        dm_embed.set_footer(text="Justice has been served ⚖️")
        dm_embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else discord.Embed.Empty)

        # Embed confirmation dans le salon
        confirm_embed = Embed(
            title="🔨 Ban effectué !",
            description=f"**{membre.mention} a été banni !**\n\n**Raison :** {raison}",
            color=discord.Color.red()
        )
        confirm_embed.set_footer(text=f"Action menée par {ctx.author}", icon_url=ctx.author.display_avatar.url)

        try:
            # Essaye d'envoyer un DM
            await membre.send(embed=dm_embed)
        except:
            pass  # DM fermés, ignore

        try:
            await ctx.guild.ban(membre, reason=raison)
            await ctx.send(embed=confirm_embed)
        except Forbidden:
            await ctx.send(f"Je n'ai pas les permissions nécessaires pour bannir {membre.mention}.")
        except Exception as e:
            await ctx.send(f"Erreur lors du bannissement : {str(e)}")


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

    @commands.hybrid_command(name="ban_multi", description="Bannit plusieurs membres à la fois.")
    @app_commands.describe(
        utilisateurs="Liste des utilisateurs à bannir (séparés par des virgules)",
        raison="Raison du ban"
    )
    @commands.has_permissions(ban_members=True)
    async def ban_multi(self, ctx, utilisateurs: str, raison: str = "Aucune raison précisée"):
        """Bannit plusieurs membres à la fois."""

        utilisateurs = [u.strip() for u in utilisateurs.split(',')]
        result_embed = Embed(title="🚫 Résultats du bannissement", color=discord.Color.red())
        result_embed.set_footer(text=f"Action par {ctx.author}", icon_url=ctx.author.display_avatar.url)

        for user_input in utilisateurs:
            member = await self.get_member(ctx, user_input)
            if member:
                try:
                    await ctx.guild.ban(member, reason=raison)
                    result_embed.add_field(name=f"✅ {member}", value="Banni avec succès", inline=False)
                except Forbidden:
                    result_embed.add_field(name=f"❌ {member}", value="Permissions insuffisantes", inline=False)
                except Exception as e:
                    result_embed.add_field(name=f"❌ {member}", value=f"Erreur : {str(e)}", inline=False)
            else:
                result_embed.add_field(name=f"❌ {user_input}", value="Utilisateur introuvable", inline=False)

        try:
            await ctx.send(embed=result_embed)
        except Forbidden:
            await ctx.author.send("Je n'ai pas pu envoyer le message de confirmation dans le canal.")

    async def get_member(self, ctx, user_input):
        """Récupère un membre via mention, ID, username ou username#discrim"""

        # Vérifie si c'est une mention
        if user_input.startswith("<@") and user_input.endswith(">"):
            user_id = user_input.strip("<@!>")
            if user_id.isdigit():
                member = ctx.guild.get_member(int(user_id))
                if member:
                    return member

        # Vérifie si c'est un ID brut
        if user_input.isdigit():
            member = ctx.guild.get_member(int(user_input))
            if member:
                return member
            # Si membre pas trouvé (peut être banni ou quitté), fetch user
            try:
                user = await self.bot.fetch_user(int(user_input))
                return user
            except:
                return None

        # Vérifie avec username#discrim
        if "#" in user_input:
            name, discrim = user_input.split("#")
            member = discord.utils.get(ctx.guild.members, name=name, discriminator=discrim)
            if member:
                return member

        # Vérifie juste le nom
        member = discord.utils.get(ctx.guild.members, name=user_input)
        return member

    @commands.hybrid_command(name='mp', description="Envoie un MP à un membre")
    async def mp(self, ctx, member: discord.Member = None, *, message: str = None):
        """Envoie un MP à un membre (commande hybride)."""
        try:
            # Validation des arguments
            if not member:
                await ctx.send("Vous devez mentionner un membre pour envoyer un MP.")
                return
            if not message:
                await ctx.send("Vous devez fournir un message à envoyer.")
                return

            await member.send(message)
            await ctx.send(f"Message envoyé à {member.mention}.")
        except discord.Forbidden:
            await ctx.send("Je ne peux pas envoyer de message à ce membre. Il a peut-être désactivé ses MP.")
        except Exception as e:
            await ctx.send(f"Une erreur est survenue : {str(e)}")
            

    @app_commands.command(name="staff", description="et préfixe le pseudomettre un membre staff")
    async def staff(self, interaction: discord.Interaction, membre: discord.Member):
        staff_roles = [1145807576353742908, 1134290681490317403, 1248046492091027548]  # Remplace par les ID des rôles staff
        for role_id in staff_roles:
            role = interaction.guild.get_role(role_id)
            if role:
                await membre.add_roles(role)

        await membre.edit(nick=f"Porn {membre.display_name}")
        await interaction.response.send_message(f"{membre.mention} a été promu en Staff", ephemeral=True)

    @app_commands.command(name="unstaff", description="enlever un membre comme staff")
    @app_commands.describe(membre="Le membre à rétrograder")
    async def unstaff(self, interaction: discord.Interaction, membre: discord.Member):
        staff_roles = [1145807576353742908, 1134290681490317403, 1248046492091027548]  # Remplace par les ID des rôles staff
        for role_id in staff_roles:
            role = interaction.guild.get_role(role_id)
            if role:
                await membre.remove_roles(role)

        if membre.nick and membre.nick.startswith("Porn "):
            await membre.edit(nick=membre.nick[8:])
        await interaction.response.send_message(f"{membre.mention} a été rétrogradé", ephemeral=True)
       
async def setup(bot: commands.Bot):
    await bot.add_cog(Utilitaire(bot))