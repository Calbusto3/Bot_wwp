import discord
import json
import os
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Button

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "autoroles.json"
        self.load_config()

    def load_config(self):
        """Charge les configurations de rôles et conditions depuis le fichier JSON."""
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as file:
                self.config = json.load(file)
        else:
            self.config = {}

    def save_config(self):
        """Sauvegarde les configurations dans le fichier JSON."""
        with open(self.config_file, "w") as file:
            json.dump(self.config, file, indent=4)

    @app_commands.command(name="setup_autorole", description="Configurer un autorôle")
    @app_commands.default_permissions(administrator=True)
    async def setup_auto_role(self, interaction: discord.Interaction):
        """Configurer un autorôle avec une interface complète de gestion."""
        embed = discord.Embed(
            title="Gestion des Autorôles",
            description="Utilisez les boutons pour gérer les autorôles du serveur.",
            color=discord.Color.green()
        )

        # Création des boutons pour activer/désactiver, ajouter, modifier, supprimer un autorôle
        button_enable = Button(label="Activer/Désactiver le système", style=discord.ButtonStyle.primary)
        button_add = Button(label="Ajouter un autorôle", style=discord.ButtonStyle.secondary)
        button_modify = Button(label="Modifier un autorôle", style=discord.ButtonStyle.secondary)
        button_remove = Button(label="Supprimer un autorôle", style=discord.ButtonStyle.danger)

        async def button_enable_callback(interaction: discord.Interaction):
            # Activation ou désactivation du système
            await interaction.response.send_message("🔄 Le système des autorôles a été activé ou désactivé.", ephemeral=True)

        async def button_add_callback(interaction: discord.Interaction):
            # Ajouter un autorôle
            await interaction.response.send_message("Veuillez sélectionner un rôle et une condition pour l'autorôle.", ephemeral=True)
            view_add = await self.create_add_view(interaction)
            await interaction.followup.send(embed=embed, view=view_add)

        async def button_modify_callback(interaction: discord.Interaction):
            # Modifier un autorôle
            await interaction.response.send_message("Sélectionnez un autorôle à modifier.", ephemeral=True)
            view_modify = await self.create_modify_view(interaction)
            await interaction.followup.send(embed=embed, view=view_modify)

        async def button_remove_callback(interaction: discord.Interaction):
            # Supprimer un autorôle
            await interaction.response.send_message("Sélectionnez un autorôle à supprimer.", ephemeral=True)
            view_remove = await self.create_remove_view(interaction)
            await interaction.followup.send(embed=embed, view=view_remove)

        # Ajout des callbacks aux boutons
        button_enable.callback = button_enable_callback
        button_add.callback = button_add_callback
        button_modify.callback = button_modify_callback
        button_remove.callback = button_remove_callback

        # Créer la vue avec les boutons
        view = View(timeout=None)
        view.add_item(button_enable)
        view.add_item(button_add)
        view.add_item(button_modify)
        view.add_item(button_remove)

        # Envoyer l'embed avec les boutons
        await interaction.response.send_message(embed=embed, view=view)

    async def create_add_view(self, interaction: discord.Interaction):
        """Création d'une vue pour ajouter un autorôle avec un rôle et une condition."""
        if not interaction.guild:
            await interaction.response.send_message("❌ Cette commande doit être exécutée dans un serveur.", ephemeral=True)
            return

        # Créer une liste des rôles dans le serveur
        roles = [discord.SelectOption(label=role.name, value=str(role.id)) for role in interaction.guild.roles]

        # Définir les conditions possibles pour l'autorôle
        conditions = [
            discord.SelectOption(label="Nouveau membre", value="Nouveau membre"),
            discord.SelectOption(label="Rejoindre un salon vocal", value="Rejoindre un salon vocal"),
            discord.SelectOption(label="Envoyer un message", value="Envoyer un message"),
            discord.SelectOption(label="Réagir à un message", value="Réagir à un message")
        ]

        select_role = Select(placeholder="Sélectionner un rôle", options=roles)
        select_condition = Select(placeholder="Sélectionner une condition", options=conditions)

        async def select_callback(interaction: discord.Interaction):
            selected_role_id = select_role.values[0]
            selected_condition = select_condition.values[0]

            # Ajouter l'autorôle à la configuration
            role = interaction.guild.get_role(int(selected_role_id))
            if role and selected_condition:
                role_condition = f"{role.id} -> {selected_condition}"
                if role_condition not in self.config:
                    self.config[role_condition] = {"role": role.id, "condition": selected_condition}
                    self.save_config()
                    await interaction.response.send_message(f"✅ L'auto-rôle `{role.name}` a été ajouté avec la condition `{selected_condition}`.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"❌ Cet autorôle `{role.name}` existe déjà.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Role ou condition non valide.", ephemeral=True)

        select_role.callback = select_callback
        select_condition.callback = select_callback

        view = View(timeout=None)
        view.add_item(select_role)
        view.add_item(select_condition)

        return view

    async def create_modify_view(self, interaction: discord.Interaction):
        """Création d'une vue pour modifier un autorôle."""
        autoroles = [discord.SelectOption(label=f"{data['role']} -> {data['condition']}", value=key) for key, data in self.config.items()]
        select_autorole = Select(placeholder="Sélectionner un autorôle à modifier", options=autoroles)

        async def select_callback(interaction: discord.Interaction):
            autorole_key = select_autorole.values[0]
            autorole_data = self.config.get(autorole_key)
            if autorole_data:
                role = interaction.guild.get_role(autorole_data['role'])
                embed = discord.Embed(
                    title="Modifier l'Autorôle",
                    description=f"Vous modifiez le rôle `{role.name}` avec la condition `{autorole_data['condition']}`.",
                    color=discord.Color.orange()
                )
                embed.add_field(name="Nouvelle Condition", value="Choisissez une nouvelle condition ou rôle.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ Autorôle introuvable.", ephemeral=True)

        select_autorole.callback = select_callback
        view = View(timeout=None)
        view.add_item(select_autorole)

        return view

    async def create_remove_view(self, interaction: discord.Interaction):
        """Création d'une vue pour supprimer un autorôle."""
        autoroles = [discord.SelectOption(label=f"{data['role']} -> {data['condition']}", value=key) for key, data in self.config.items()]
        select_autorole = Select(placeholder="Sélectionner un autorôle à supprimer", options=autoroles)

        async def select_callback(interaction: discord.Interaction):
            autorole_key = select_autorole.values[0]
            self.config.pop(autorole_key, None)
            self.save_config()
            await interaction.response.send_message(f"✅ L'auto-rôle `{autorole_key}` a été supprimé.", ephemeral=True)

        select_autorole.callback = select_callback
        view = View(timeout=None)
        view.add_item(select_autorole)

        return view

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Attribuer un autorôle à un nouveau membre."""
        for _, data in self.config.items():
            if data["condition"] == "Nouveau membre":
                role = member.guild.get_role(data["role"])
                if role:
                    await member.add_roles(role)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Attribuer un autorôle si un membre rejoint un salon vocal ou envoie un message."""
        for _, data in self.config.items():
            role = after.guild.get_role(data["role"])
            if data["condition"] == "Rejoindre un salon vocal" and before.voice is None and after.voice:
                if role:
                    await after.add_roles(role)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Attribuer un autorôle si un membre envoie un message."""
        if message.author.bot:
            return
        for _, data in self.config.items():
            if data["condition"] == "Envoyer un message":
                role = message.guild.get_role(data["role"])
                if role:
                    await message.author.add_roles(role)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Attribuer un autorôle si un utilisateur réagit à un message."""
        for _, data in self.config.items():
            if data["condition"] == "Réagir à un message":
                role = user.guild.get_role(data["role"])
                if role:
                    await user.add_roles(role)

async def setup(bot):
    await bot.add_cog(AutoRole(bot))
