import discord
import json
import os
import uuid
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Button


class AutoRole(commands.Cog):
    """Cog pour gérer les autorôles interactifs."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config_file = "autoroles.json"
        self.config = {}
        self.load_config()

    def load_config(self) -> None:
        """Charge les configurations de rôles et conditions depuis le fichier JSON."""
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as file:
                self.config = json.load(file)
        else:
            self.config = {"autoroles": []}

    def save_config(self) -> None:
        """Sauvegarde les configurations dans le fichier JSON."""
        with open(self.config_file, "w") as file:
            json.dump(self.config, file, indent=4)

    @staticmethod
    def create_button(label: str, style: discord.ButtonStyle, callback) -> Button:
        """Crée un bouton avec un callback."""
        button = Button(label=label, style=style)
        button.callback = callback
        return button

    @app_commands.command(name="setup_autorole", description="Configurer un autorôle")
    @app_commands.default_permissions(administrator=True)
    async def setup_auto_role(self, interaction: discord.Interaction) -> None:
        """Configurer un autorôle avec une interface complète de gestion."""
        await self.send_main_embed(interaction)

    async def send_main_embed(self, interaction: discord.Interaction, message: discord.Message = None) -> None:
        """Envoie ou met à jour l'embed principal."""
        embed = discord.Embed(
            title="Gestion des Autorôles",
            description="Utilisez les boutons pour gérer les autorôles du serveur.",
            color=discord.Color.green()
        )

        # Ajouter les autorôles existants à l'embed
        if self.config["autoroles"]:
            for autorole in self.config["autoroles"]:
                role = interaction.guild.get_role(autorole["role"])
                if role:
                    embed.add_field(
                        name=f"{role.name} -> {autorole['condition']}",
                        value=f"Statut : {'✅ Activé' if autorole['enabled'] else '❌ Désactivé'}",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="Rôle introuvable",
                        value="❌ Ce rôle a été supprimé ou n'est plus accessible.",
                        inline=False
                    )
        else:
            embed.description += "\n\n*Aucun autorôle configuré.*"

        # Boutons interactifs
        button_enable = self.create_button(
            "Activer/Désactiver le système",
            discord.ButtonStyle.green if self.config.get("enabled", True) else discord.ButtonStyle.red,
            self.toggle_system
        )
        button_add = self.create_button("Ajouter un autorôle", discord.ButtonStyle.secondary, self.send_add_embed)
        button_modify = self.create_button("Modifier un autorôle", discord.ButtonStyle.secondary, self.send_modify_embed)
        button_remove = self.create_button("Supprimer un autorôle", discord.ButtonStyle.danger, self.send_remove_embed)

        # Créer la vue avec les boutons
        view = View(timeout=300)
        view.add_item(button_enable)
        view.add_item(button_add)
        view.add_item(button_modify)
        view.add_item(button_remove)

        # Envoyer ou mettre à jour le message
        if message:
            await message.edit(embed=embed, view=view)
        else:
            await interaction.response.send_message(embed=embed, view=view)

    async def toggle_system(self, interaction: discord.Interaction) -> None:
        """Active ou désactive le système d'autorôles."""
        self.config["enabled"] = not self.config.get("enabled", True)
        self.save_config()
        await self.send_main_embed(interaction, message=interaction.message)

    async def send_add_embed(self, interaction: discord.Interaction, message: discord.Message = None) -> None:
        """Envoie ou met à jour l'embed pour ajouter un autorôle."""
        embed = discord.Embed(
            title="Ajouter un Autorôle",
            description="Sélectionnez un rôle et une condition pour l'autorôle.",
            color=discord.Color.blue()
        )

        # Créer une liste des rôles dans le serveur
        roles = [
            discord.SelectOption(label=role.name, value=str(role.id))
            for role in interaction.guild.roles if role < interaction.guild.me.top_role
        ]

        # Définir les conditions possibles pour l'autorôle
        conditions = [
            discord.SelectOption(label="Nouveau membre", value="Nouveau membre"),
            discord.SelectOption(label="Rejoindre un salon vocal", value="Rejoindre un salon vocal"),
            discord.SelectOption(label="Envoyer un message", value="Envoyer un message"),
            discord.SelectOption(label="Réagir à un message", value="Réagir à un message")
        ]

        select_role = Select(placeholder="Sélectionner un rôle", options=roles)
        select_condition = Select(placeholder="Sélectionner une condition", options=conditions)
        button_back = Button(label="Retour", style=discord.ButtonStyle.secondary)

        async def select_callback(interaction: discord.Interaction):
            selected_role_id = select_role.values[0]
            selected_condition = select_condition.values[0]

            # Ajouter l'autorôle à la configuration
            role = interaction.guild.get_role(int(selected_role_id))
            if any(ar["role"] == int(selected_role_id) and ar["condition"] == selected_condition for ar in self.config["autoroles"]):
                await interaction.response.send_message("❌ Cet autorôle existe déjà.", ephemeral=True)
                return

            self.config["autoroles"].append({
                "id": str(uuid.uuid4())[:8],
                "role": int(selected_role_id),
                "condition": selected_condition,
                "enabled": True
            })
            self.save_config()
            await self.send_main_embed(interaction, message=message)

        async def button_back_callback(interaction: discord.Interaction):
            await self.send_main_embed(interaction, message=message)

        select_role.callback = select_callback
        select_condition.callback = select_callback
        button_back.callback = button_back_callback

        view = View(timeout=None)
        view.add_item(select_role)
        view.add_item(select_condition)
        view.add_item(button_back)

        if message:
            await message.edit(embed=embed, view=view)
        else:
            await interaction.response.send_message(embed=embed, view=view)

    async def send_modify_embed(self, interaction: discord.Interaction, message: discord.Message = None) -> None:
        """Envoie ou met à jour l'embed pour modifier un autorôle."""
        embed = discord.Embed(
            title="Modifier un Autorôle",
            description="Sélectionnez un autorôle à modifier.",
            color=discord.Color.orange()
        )

        # Créer une liste des autorôles existants
        options = [
            discord.SelectOption(label=f"{interaction.guild.get_role(ar['role']).name} -> {ar['condition']}", value=ar["id"])
            for ar in self.config["autoroles"] if interaction.guild.get_role(ar["role"])
        ]

        if not options:
            await interaction.response.send_message("❌ Aucun autorôle à modifier.", ephemeral=True)
            return

        select = Select(placeholder="Sélectionnez un autorôle", options=options)
        button_back = Button(label="Retour", style=discord.ButtonStyle.secondary)

        async def select_callback(interaction: discord.Interaction):
            selected_id = select.values[0]
            autorole = next((ar for ar in self.config["autoroles"] if ar["id"] == selected_id), None)
            if not autorole:
                await interaction.response.send_message("❌ Autorôle introuvable.", ephemeral=True)
                return

            # Afficher une modale ou une autre interface pour modifier l'autorôle
            await interaction.response.send_message("Modification non implémentée.", ephemeral=True)

        async def button_back_callback(interaction: discord.Interaction):
            await self.send_main_embed(interaction, message=message)

        select.callback = select_callback
        button_back.callback = button_back_callback

        view = View(timeout=None)
        view.add_item(select)
        view.add_item(button_back)

        if message:
            await message.edit(embed=embed, view=view)
        else:
            await interaction.response.send_message(embed=embed, view=view)

    async def send_remove_embed(self, interaction: discord.Interaction, message: discord.Message = None) -> None:
        """Envoie ou met à jour l'embed pour supprimer un autorôle."""
        embed = discord.Embed(
            title="Supprimer un Autorôle",
            description="Sélectionnez un autorôle à supprimer.",
            color=discord.Color.red()
        )

        # Créer une liste des autorôles existants
        options = [
            discord.SelectOption(label=f"{interaction.guild.get_role(ar['role']).name} -> {ar['condition']}", value=ar["id"])
            for ar in self.config["autoroles"] if interaction.guild.get_role(ar["role"])
        ]

        if not options:
            await interaction.response.send_message("❌ Aucun autorôle à supprimer.", ephemeral=True)
            return

        select = Select(placeholder="Sélectionnez un autorôle", options=options)
        button_back = Button(label="Retour", style=discord.ButtonStyle.secondary)

        async def select_callback(interaction: discord.Interaction):
            selected_id = select.values[0]
            self.config["autoroles"] = [ar for ar in self.config["autoroles"] if ar["id"] != selected_id]
            self.save_config()
            await self.send_main_embed(interaction, message=message)

        async def button_back_callback(interaction: discord.Interaction):
            await self.send_main_embed(interaction, message=message)

        select.callback = select_callback
        button_back.callback = button_back_callback

        view = View(timeout=None)
        view.add_item(select)
        view.add_item(button_back)

        if message:
            await message.edit(embed=embed, view=view)
        else:
            await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot) -> None:
    """Ajoute le cog au bot."""
    await bot.add_cog(AutoRole(bot))
