import discord
from discord.ext import commands
from discord.ui import View, Select, Button
import os

class TicketSystem(commands.Cog):
    """Système de tickets avec menu déroulant et gestion avancée."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ticket_categories = {
            "partenariat": {"description": "Faire une demande de partenariat", "category_id": 1371176734434529361, "role_ping": 1371177529297342564},
            "se vérifier": {"description": "Se faire vérifier", "category_id": 1371177186937278554, "role_ping": 1371177629570568264},
            "recrutement": {"description": "Se faire recruter", "category_id": 1371178636085956658, "role_ping": 1371177973448970270},
            "fake": {"description": "Signaler un membre fake", "category_id": 1371178690154860604, "role_ping": 1371177906461737143},
            "report": {"description": "Reporter un membre", "category_id": 1371178818596896911, "role_ping": 1371177679315009668},
            "autre": {"description": "Pour une autre raison", "category_id": 1371185321043165274, "role_ping": 1371177752975249561},
        }
        self.ticket_log_channel_id = 1355619861153317004  # ID du salon log des tickets
        self.ticket_counter = 0  # Compteur pour les numéros de tickets

    @commands.Cog.listener()
    async def on_ready(self):
        print("🎫 Système de tickets prêt !")

    @commands.command(name="setup_ticket", description="Configurer le système de tickets.")
    @commands.has_permissions(administrator=True)
    async def setup_ticket(self, ctx: commands.Context):
        """Commande pour configurer le système de tickets."""
        embed = discord.Embed(
            title="🎫 Système de Tickets",
            description=(
                "Pour contacter le staff, sélectionnez une raison en utilisant le menu déroulant ci-dessous pour ouvrir un ticket.\n"
                "> Il est inutile de ping le staff dans votre ticket, il sera pris en charge dès que possible par un membre du staff.\n\n"
                "Toute forme d'abus (ouverture inutile, troll, etc.) sera sévèrement sanctionnée."
            ),
            color=discord.Color.blue()
        )

        # Menu déroulant pour sélectionner une raison
        select = Select(placeholder="Choisissez une raison", options=[
            discord.SelectOption(label=reason.capitalize(), description=data["description"], value=reason)
            for reason, data in self.ticket_categories.items()
        ])
        select.callback = self.create_ticket

        view = View(timeout=None)
        view.add_item(select)

        await ctx.send(embed=embed, view=view)

    async def create_ticket(self, interaction: discord.Interaction):
        """Créer un ticket en fonction de la raison sélectionnée."""
        reason = interaction.data["values"][0]
        category_data = self.ticket_categories.get(reason)

        if not category_data:
            await interaction.response.send_message("❌ Une erreur est survenue. Veuillez réessayer.", ephemeral=True)
            return

        guild = interaction.guild
        category = discord.utils.get(guild.categories, id=category_data["category_id"])

        # Vérifier si la catégorie existe
        if not category:
            await interaction.response.send_message("❌ La catégorie associée à cette raison n'existe pas.", ephemeral=True)
            return

        # Vérifier si l'utilisateur a déjà un ticket ouvert
        existing_channel = discord.utils.get(category.channels, name=f"t-{interaction.user.id}")
        if existing_channel:
            await interaction.response.send_message("❌ Vous avez déjà un ticket ouvert.", ephemeral=True)
            return

        # Créer un salon pour le ticket
        self.ticket_counter += 1
        ticket_name = f"t-{self.ticket_counter} | {interaction.user.name}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        ticket_channel = await category.create_text_channel(name=ticket_name, overwrites=overwrites)

        # Envoyer un message dans le salon du ticket
        embed = discord.Embed(
            title=f"🎫 Ticket - {reason.capitalize()}",
            description="Expliquez votre problème ici. Un membre du staff vous répondra bientôt.",
            color=discord.Color.green()
        )
        role_ping = guild.get_role(category_data["role_ping"])
        close_button = Button(label="Fermer", style=discord.ButtonStyle.red)
        close_button.callback = lambda i: self.close_ticket(i, ticket_channel, interaction.user)

        view = View(timeout=None)
        view.add_item(close_button)

        await ticket_channel.send(
            content=f"{interaction.user.mention}, bienvenue dans votre ticket ! {role_ping.mention if role_ping else ''}",
            embed=embed,
            view=view
        )
        await interaction.response.send_message(f"✅ Ticket créé : {ticket_channel.mention}", ephemeral=True)

    async def close_ticket(self, interaction: discord.Interaction, channel: discord.TextChannel, ticket_owner: discord.Member):
        """Fermer un ticket."""
        # Modifier les permissions pour retirer l'accès au membre
        await channel.set_permissions(ticket_owner, read_messages=False, send_messages=False)

        # Renommer le salon pour indiquer qu'il est fermé
        await channel.edit(name=f"{channel.name} - fermé")

        # Envoyer un message indiquant que le ticket est fermé
        embed = discord.Embed(
            title="Ticket fermé",
            description=f"Ticket fermé par {interaction.user.mention}.",
            color=discord.Color.red()
        )
        reopen_button = Button(label="Réouvrir", style=discord.ButtonStyle.green)
        delete_button = Button(label="Supprimer", style=discord.ButtonStyle.danger)

        reopen_button.callback = lambda i: self.reopen_ticket(i, channel, ticket_owner)
        delete_button.callback = lambda i: self.delete_ticket(i, channel)

        view = View(timeout=None)
        view.add_item(reopen_button)
        view.add_item(delete_button)

        await channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Ticket fermé.", ephemeral=True)

    async def reopen_ticket(self, interaction: discord.Interaction, channel: discord.TextChannel, ticket_owner: discord.Member):
        """Réouvrir un ticket."""
        # Redonner l'accès au membre
        await channel.set_permissions(ticket_owner, read_messages=True, send_messages=True)

        # Renommer le salon pour indiquer qu'il est réouvert
        await channel.edit(name=channel.name.replace(" - fermé", ""))

        # Envoyer un message indiquant que le ticket est réouvert
        embed = discord.Embed(
            title="Ticket réouvert",
            description=f"Ticket réouvert par {interaction.user.mention}.",
            color=discord.Color.green()
        )
        await channel.send(embed=embed)
        await interaction.response.send_message("✅ Ticket réouvert.", ephemeral=True)

    async def delete_ticket(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Supprimer un ticket et envoyer les logs."""
        # Récupérer l'historique des messages
        messages = await channel.history(limit=None, oldest_first=True).flatten()
        log_content = "\n".join([f"[{msg.created_at}] {msg.author}: {msg.content}" for msg in messages])

        # Envoyer les logs dans le salon dédié
        log_channel = self.bot.get_channel(self.ticket_log_channel_id)
        if log_channel and log_content.strip():
            await log_channel.send(
                content=f"Logs du ticket {channel.name} :",
                file=discord.File(fp=log_content, filename=f"{channel.name}.txt")
            )

        # Supprimer le salon
        await channel.delete()
        await interaction.response.send_message("Ticket supprimé.", ephemeral=True)


async def setup(bot: commands.Bot):
    """Ajoute le cog au bot."""
    await bot.add_cog(TicketSystem(bot))