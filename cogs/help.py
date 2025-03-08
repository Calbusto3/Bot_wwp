from discord.ext import commands
from discord import Embed, Color, Interaction, SelectOption
from discord.ui import View, Select
import discord
from datetime import datetime, timedelta
import asyncio

class InfoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="infos", description="Obtenir des informations sur le bot et ses commandes.")
    async def infos(self, ctx: commands.Context):
        # Vérification des permissions : l'utilisateur doit avoir la permission 'Gérer les messages'
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send("❌ Vous n'avez pas la permission d'utiliser cette commande.")
            return

        # Création de l'embed de base
        embed = discord.Embed(
            title="Informations sur le Bot",
            description="Je suis le bot officiel de World War Porn, voici quelques informations à mon sujet.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Créateur du bot", value="@.Calbusto (ID: 1033834366822002769)", inline=False)
        embed.add_field(name="Date de création du bot", value="29 janvier 2025 (V2.1.1)", inline=False)
        embed.add_field(name="Sélectionnez une commande", value="Utilisez le menu déroulant ci-dessous pour obtenir des informations sur une commande.", inline=False)

        # Création du sélecteur pour choisir une commande
        select = Select(
            placeholder="Choisissez une commande pour plus d'informations",
            options=[
                discord.SelectOption(label="/supprimer", description="supprimer un nombre définit de message dans un salon.", value="supprimer"),
                discord.SelectOption(label="/envoyer", description="Envoyer un message sous l'identité du bot.", value="envoyer"),
                discord.SelectOption(label="/ban_multi", description="Bannir plusieurs membre à la foi", value="ban_multi"),
                discord.SelectOption(label="/bannir", description="Bannir un membre", value="bannir"),
                discord.SelectOption(label="/unbannir", description="Débannir un membre", value="unbannir"),
                discord.SelectOption(label="/muter", description="Mute un membre", value="muter"),
                discord.SelectOption(label="/unmuter", description="Unmute un membre", value="unmuter"),
                discord.SelectOption(label="/fake", description="afficher un membre comme fake", value="fake"),
                discord.SelectOption(label="/unfake", description="enlever un membre comme fake", value="unfake"),
                discord.SelectOption(label="/message_all", description="Envoyer un message à tous les membres", value="message_all"),
                discord.SelectOption(label="/envoyer", description="Envoyer un message sous l'identité du bot", value="envoyer"),
                discord.SelectOption(label="/mp", description="Envoyer un message privé à un membre", value="mp"),
                discord.SelectOption(label="/staff", description="Mettre un membre staff", value="staff"),
        
        
        
            ]
        )

        # Fonction de réponse pour le sélecteur
        async def select_callback(interaction: discord.Interaction):
            selected_value = select.values[0]
            
            if selected_value == "staff":
                info_embed = discord.Embed(
                    title="Commande /staff | /unstaff",
                    description="mettre ou enlever un membre comme étant staff.",
                    color=discord.Color.red()
                )
                info_embed.add_field(name="Usage", value="/staff [''membre''] | unstaff [''membre'']", inline=False)
                info_embed.add_field(name="Exemple", value="/staff @utilisateur | unstaff @utilisateur", inline=False)
                info_embed.add_field(name="Permission requise", value="Administrateur", inline=False)
                info_embed.add_field(name="Utilisable avec préfixe (+)", value="oui", inline=False)
                info_embed.add_field(name="Autre commande(s) du style", value="Aucune", inline=False)


            elif selected_value == "unfake":
                info_embed = discord.Embed(
                    title="Commande /unfake",
                    description="Cette commande permet d'enlever quelqu'un comme fake, un message sera envoyé automatiquement dans <#1250466390675292201> pour annoncer que le membre n'est plus fake.",
                    color=discord.Color.red()
                )
                info_embed.add_field(name="Usage", value="/unfake [''membre'']", inline=False)
                info_embed.add_field(name="Exemple", value="/fake @utilisateur", inline=False)
                info_embed.add_field(name="Permission requise", value="Gérer les salons | modérateur", inline=False)
                info_embed.add_field(name="Utilisable avec préfixe (+)", value="oui", inline=False)
                info_embed.add_field(name="Autre commande(s) du style", value="Aucune", inline=False)

            elif selected_value == "fake":
                info_embed = discord.Embed(
                    title="Commande /fake",
                    description="Cette commande permet d'afficher un membre comme étant fake (générallement utiliser pour les femme qui refusent de se faire vérifier.)\nun message d'annonce est automatiquement envoyé dans le salon <#1250466390675292201>. Vous pouvez exécutez la commande où vous voulez\n- option **avertir** : si True est entré comme valeur, le bot va envoyé un message après l'exécution de la commande au membre selectionner pour l'avertir qu'il a été afficher comme fake et les instructions nécessaire (facultatif).\n- option **preuves** : mettre une image comme preuve à l'appui (facultatif).",
                    color=discord.Color.red()
                )
                info_embed.add_field(name="Usage", value="/fake [''membre''] [''avertir (optionnel)''] [''image de preuves optionnel'']", inline=False)
                info_embed.add_field(name="Exemple", value="/fake @utilisateur True/Fals [image/ou non]", inline=False)
                info_embed.add_field(name="Permission requise", value="Gérer les salons | modérateur", inline=False)
                info_embed.add_field(name="Utilisable avec préfixe (+)", value="oui", inline=False)
                info_embed.add_field(name="Autre commande(s) du style", value="Aucune", inline=False)

            elif selected_value == "supprimer":
                info_embed = discord.Embed(
                    title="Commande /supprimer",
                    description="Cette commande permet de supprimer plusieurs messages à la foi dans un salon.",
                    color=discord.Color.red()
                )
                info_embed.add_field(name="Usage", value="/supprimer [''nombre'']", inline=False)
                info_embed.add_field(name="Exemple", value="/supprimer 5]", inline=False)
                info_embed.add_field(name="Permission requise", value="Gérer les messages | modérateur", inline=False)
                info_embed.add_field(name="Utilisable avec préfixe (+)", value="oui", inline=False)
                info_embed.add_field(name="Autre commande(s) du style", value="Aucune", inline=False)

        
            elif selected_value == "envoyer":
                info_embed = discord.Embed(
                    title="Commande /envoyer",
                    description="Cette commande permet d'envoyé un message sous l'identité du bot.",
                    color=discord.Color.red()
                )
                info_embed.add_field(name="Usage", value="/envoyer [''message'']", inline=False)
                info_embed.add_field(name="Exemple", value="/envoyer ''bonjour c'est le bot''", inline=False)
                info_embed.add_field(name="Permission requise", value="Administrateur", inline=False)
                info_embed.add_field(name="Utilisable avec préfixe (+)", value="oui", inline=False)
                info_embed.add_field(name="Autre commande(s) du style", value="Aucune", inline=False)
  
            elif selected_value == "ban_multi":
                info_embed = discord.Embed(
                    title="Commande /ban_multi",
                    description="Cette commande permet de bannir plusieurs memnre à la foi du serveur..",
                    color=discord.Color.red()
                )
                info_embed.add_field(name="Usage", value="/ban_multi [NomUtilisateur],[IdMembre],[Idmembre],[NomUtilisateur] [raison]", inline=False)
                info_embed.add_field(name="Exemple", value="/ban_multi @NomUtilisateur,@NomUtilisateur,NomUtilisateur,Id,Id Spam", inline=False)
                info_embed.add_field(name="Permission requise", value="Administrateur", inline=False)
                info_embed.add_field(name="Utilisable avec préfixe (+)", value="oui", inline=False)
                info_embed.add_field(name="Autre commande(s) du style", value="bannir.", inline=False)

            elif selected_value == "bannir":
                info_embed = discord.Embed(
                    title="Commande /bannir",
                    description="Cette commande permet de bannir un membre du serveur.",
                    color=discord.Color.red()
                )
                info_embed.add_field(name="Usage", value="/bannir [membre] [raison]", inline=False)
                info_embed.add_field(name="Exemple", value="/bannir @utilisateur Spam", inline=False)
                info_embed.add_field(name="Permission requise", value="gestion des membres | modérateur", inline=False)
                info_embed.add_field(name="Utilisable avec préfixe (+)", value="oui", inline=False)
                info_embed.add_field(name="Autre commande(s) du style", value="ban_multi.", inline=False)

            elif selected_value == "unbannir":
                info_embed = discord.Embed(
                    title="Commande /unbannir",
                    description="Cette commande permet de débannir un membre du serveur.",
                    color=discord.Color.green()
                )
                info_embed.add_field(name="Usage", value="/unbannir [ID du membre]", inline=False)
                info_embed.add_field(name="Exemple", value="/unbannir 123456789012345678", inline=False)
                info_embed.add_field(name="Permission requise", value="oui", inline=False)
                info_embed.add_field(name="Utilisable avec préfixe (+)", value="Gérer les membres | modérateur", inline=False)
                info_embed.add_field(name="Autre commande(s) du style", value="Aucune.", inline=False)

            elif selected_value == "muter":
                info_embed = discord.Embed(
                    title="Commande /muter",
                    description="Cette commande permet de muter un membre pendant une durée spécifiée.",
                    color=discord.Color.orange()
                )
                info_embed.add_field(name="Usage", value="/muter [membre] [durée] [raison]", inline=False)
                info_embed.add_field(name="Exemple", value="/muter @utilisateur 10 Spam", inline=False)
                info_embed.add_field(name="Permission requise", value="Gestion des membres | modérateur", inline=False)
                info_embed.add_field(name="Autre commande(s) du style", value="Aucune", inline=False)

            elif selected_value == "unmuter":
                info_embed = discord.Embed(
                    title="Commande /unmuter",
                    description="Cette commande permet de démuter un membre.",
                    color=discord.Color.blue())
                info_embed.add_field(name="Usage", value="/unmuter [membre]", inline=False)
                info_embed.add_field(name="Exemple", value="/unmuter @utilisateur", inline=False)
                info_embed.add_field(name="Permission requise", value="Gestion des membres | modérateur", inline=False)
                info_embed.add_field(name="Utilisable avec préfixe (+)", value="oui", inline=False)
                info_embed.add_field(name="Autre commande(s) du style", value="Aucune.", inline=False)

            elif selected_value == "message_all":
                info_embed = discord.Embed(
                    title="Commande /message_all",
                    description="Cette commande permet d'envoyer un message à tous les membres du serveur.",
                    color=discord.Color.blue()
                )
                info_embed.add_field(name="Usage", value="/message_all [message]", inline=False)
                info_embed.add_field(name="Exemple", value="/message_all Attention à tous !", inline=False)
                info_embed.add_field(name="Utilisable avec préfixe (+)", value="oui", inline=False)
                info_embed.add_field(name="Permission requise", value="Administrateur", inline=False)

            elif selected_value == "mp":
                info_embed = discord.Embed(
                    title="Commande /mp",
                    description="Cette commande permet d'envoyer un message privé à un membre mentionné.",
                    color=discord.Color.purple()
                )
                info_embed.add_field(name="Usage", value="/mp [membre] [message]", inline=False)
                info_embed.add_field(name="Exemple", value="/mp @utilisateur Salut !", inline=False)
                info_embed.add_field(name="Utilisable avec préfixe (+)", value="oui", inline=False)
                info_embed.add_field(name="Permission requise", value="Administrateur", inline=False)


        select.callback = select_callback

        # Créer la vue avec le sélecteur
        view = View()
        view.add_item(select)

        # Envoi de l'embed initial avec le sélecteur
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(InfoCommand(bot))