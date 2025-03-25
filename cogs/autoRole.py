import discord
from discord.ext import commands
from discord.ui import Button, View, Select, SelectOption
from discord import ButtonStyle, Interaction
import json
import os

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

    async def setup_auto_role(self, interaction: Interaction):
        """Configurer un nouvel autorôle."""
        # Sélection du rôle
        await interaction.response.send_message("Quel rôle souhaitez-vous attribuer ?", ephemeral=True)
        role_message = await self.bot.wait_for('message', check=lambda m: m.author == interaction.user and m.channel == interaction.channel)
        role = discord.utils.get(interaction.guild.roles, name=role_message.content.strip())

        if not role:
            await interaction.followup.send("❌ Le rôle spécifié n'existe pas.", ephemeral=True)
            return

        # Sélection de la condition
        await interaction.followup.send(
            "Choisissez un cas parmi les suivants :\n1. Nouveau membre\n2. Rejoindre un salon vocal\n3. Envoyer un message dans un salon\n4. Réagir à un message",
            ephemeral=True
        )
        condition_message = await self.bot.wait_for('message', check=lambda m: m.author == interaction.user and m.channel == interaction.channel)
        condition = condition_message.content.strip()

        # Ajouter la condition et le rôle à la configuration
        role_condition = f"{role.name} -> {condition}"
        if role_condition not in self.config:
            self.config[role_condition] = {
                "role": role.name,
                "condition": condition
            }
            self.save_config()
            await interaction.followup.send(f"✅ L'auto-rôle `{role.name}` a été ajouté avec la condition `{condition}`.", ephemeral=True)
        else:
            await interaction.followup.send("❌ Cet autorôle existe déjà.", ephemeral=True)

    async def remove_auto_role(self, interaction: Interaction):
        """Supprimer un autorôle existant."""
        options = [SelectOption(label=f"{data['role']} -> {data['condition']}", value=key) for key, data in self.config.items()]
        select = Select(placeholder="Sélectionne l'autorôle à supprimer", options=options)

        async def select_callback(interaction: Interaction):
            autorole_key = select.values[0]
            autorole = self.config.pop(autorole_key, None)

            if autorole:
                self.save_config()
                await interaction.response.edit_message(content=f"✅ L'auto-rôle `{autorole_key}` a été supprimé.", embed=None)
            else:
                await interaction.response.send_message("❌ Autorôle introuvable.", ephemeral=True)

        select.callback = select_callback

        embed = discord.Embed(
            title="Supprimer un autorôle",
            description="Sélectionne un autorôle à supprimer.",
            color=discord.Color.red()
        )

        await interaction.response.send_message(embed=embed, view=View(select))

    async def show_auto_roles(self, interaction: Interaction):
        """Afficher tous les autorôles configurés."""
        if not self.config:
            await interaction.response.send_message("❌ Aucun autorôle configuré.", ephemeral=True)
            return

        options = [SelectOption(label=f"{data['role']} -> {data['condition']}", value=key) for key, data in self.config.items()]
        select = Select(placeholder="Sélectionne un autorôle à voir", options=options)

        async def select_callback(interaction: Interaction):
            autorole_key = select.values[0]
            autorole = self.config.get(autorole_key)

            if autorole:
                embed = discord.Embed(
                    title="Détails de l'Autorôle",
                    description=f"**Rôle** : {autorole['role']}\n**Condition** : {autorole['condition']}",
                    color=discord.Color.green()
                )
                await interaction.response.edit_message(embed=embed)
            else:
                await interaction.response.send_message("❌ Autorôle introuvable.", ephemeral=True)

        select.callback = select_callback

        embed = discord.Embed(
            title="Afficher les autorôles",
            description="Sélectionne un autorôle pour afficher les détails.",
            color=discord.Color.blue()
        )

        await interaction.response.send_message(embed=embed, view=View(select))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Attribuer un autorôle à un nouveau membre."""
        for condition, data in self.config.items():
            if data["condition"] == "Nouveau membre":
                role = discord.utils.get(member.guild.roles, name=data["role"])
                if role:
                    await member.add_roles(role)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Attribuer un autorôle si un membre rejoint un salon vocal ou envoie un message dans un salon."""
        for condition, data in self.config.items():
            role = discord.utils.get(after.guild.roles, name=data["role"])

            if condition == "Rejoindre un salon vocal" and before.voice is None and after.voice:
                if role:
                    await after.add_roles(role)

            if condition == "Envoyer un message dans un salon" and after.guild.get_channel(data["condition"]):
                if role:
                    await after.add_roles(role)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Attribuer un autorôle si un utilisateur réagit à un message."""
        for condition, data in self.config.items():
            if condition == "Réagir à un message":
                role = discord.utils.get(user.guild.roles, name=data["role"])
                if role:
                    await user.add_roles(role)

async def setup(bot):
    await bot.add_cog(AutoRole(bot))