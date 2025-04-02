import discord
from discord.ext import commands
from discord.ui import View, Button, Select
from typing import Optional
import json
import os

class ConfigEvent(commands.Cog):
    CONFIG_FILE = "configurations.json"

    def __init__(self, bot):
        self.bot = bot
        self.configurations = self.load_configurations()

    def save_configurations(self):
        """Sauvegarde les configurations dans un fichier JSON."""
        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.configurations, f, indent=4)

    def load_configurations(self):
        """Charge les configurations depuis un fichier JSON."""
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    @commands.command(name="config_event", description="Configurer des événements conditionnels.")
    @commands.has_permissions(administrator=True)
    async def config_event(self, ctx):
        """Commande principale pour configurer les événements."""
        embed = discord.Embed(
            title="⚙️ Configuration des événements",
            description="Utilisez les boutons ci-dessous pour gérer les configurations.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Ajouter une condition", value="Ajoutez une nouvelle condition à un événement.", inline=False)
        embed.add_field(name="Modifier une configuration", value="Modifiez une configuration existante.", inline=False)
        embed.add_field(name="Supprimer une configuration", value="Supprimez une configuration existante.", inline=False)

        view = ConfigEventView(self)
        await ctx.send(embed=embed, view=view)

    async def execute_action(self, guild_id: int, action: str, channel_id: int, role_id: int, member: discord.Member):
        """Exécute une action configurée si les conditions sont remplies."""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            print(f"⚠️ Salon introuvable : {channel_id}")
            return

        role = guild.get_role(role_id)
        if not role:
            print(f"⚠️ Rôle introuvable : {role_id}")
            return

        if role in member.roles:
            if action == "send_message":
                await channel.send(f"{member.mention}, une action configurée a été déclenchée !")
            elif action == "send_file":
                await channel.send(file=discord.File("path/to/your/file.png"))
            elif action == "send_emoji":
                await channel.send("🎉")
            elif action == "react_message":
                async for message in channel.history(limit=1):
                    await message.add_reaction("👍")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Détecte les changements de rôle d'un membre et exécute les actions configurées."""
        if before.roles == after.roles:
            return  # Aucun changement de rôle

        added_roles = [role for role in after.roles if role not in before.roles]
        for guild_id, configs in self.configurations.items():
            for config in configs:
                if config["role_id"] in [role.id for role in added_roles]:
                    await self.execute_action(
                        guild_id=guild_id,
                        action=config["action"],
                        channel_id=config["channel_id"],
                        role_id=config["role_id"],
                        member=after
                    )

class ConfigEventView(View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

        # Bouton pour ajouter une condition
        self.add_item(Button(label="Ajouter une condition", style=discord.ButtonStyle.green, custom_id="add_condition"))

        # Bouton pour modifier une configuration
        self.add_item(Button(label="Modifier une configuration", style=discord.ButtonStyle.blurple, custom_id="modify_config"))

        # Bouton pour supprimer une configuration
        self.add_item(Button(label="Supprimer une configuration", style=discord.ButtonStyle.red, custom_id="delete_config"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Vérifie si l'utilisateur est administrateur."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Vous devez être administrateur pour utiliser cette commande.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Ajouter une condition", style=discord.ButtonStyle.green)
    async def add_condition(self, interaction: discord.Interaction, button: Button):
        """Ajoute une nouvelle condition."""
        embed = discord.Embed(
            title="➕ Ajouter une condition",
            description="Sélectionnez une action à effectuer lorsque la condition est remplie.",
            color=discord.Color.green()
        )
        select = Select(
            placeholder="Choisissez une action",
            options=[
                discord.SelectOption(label="Envoyer un message", value="send_message"),
                discord.SelectOption(label="Envoyer un fichier", value="send_file"),
                discord.SelectOption(label="Envoyer une émoji", value="send_emoji"),
                discord.SelectOption(label="Réagir à un message", value="react_message")
            ]
        )

        async def select_callback(interaction: discord.Interaction):
            action = select.values[0]
            await interaction.response.send_message(f"Action sélectionnée : {action}", ephemeral=True)
            # Étape suivante : Sélectionner le salon
            await self.select_channel(interaction, action)

        select.callback = select_callback
        view = View()
        view.add_item(select)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def select_channel(self, interaction: discord.Interaction, action: str):
        """Permet de sélectionner un salon pour l'action."""
        embed = discord.Embed(
            title="📢 Sélectionner un salon",
            description="Choisissez le salon où l'action sera effectuée.",
            color=discord.Color.orange()
        )
        select = Select(
            placeholder="Choisissez un salon",
            options=[
                discord.SelectOption(label=channel.name, value=str(channel.id))
                for channel in interaction.guild.text_channels
            ]
        )

        async def select_callback(interaction: discord.Interaction):
            channel_id = int(select.values[0])
            await interaction.response.send_message(f"Salon sélectionné : <#{channel_id}>", ephemeral=True)
            # Étape suivante : Ajouter des rôles éligibles/ignorés
            await self.select_roles(interaction, action, channel_id)

        select.callback = select_callback
        view = View()
        view.add_item(select)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def select_roles(self, interaction: discord.Interaction, action: str, channel_id: int):
        """Permet de sélectionner des rôles éligibles ou ignorés."""
        embed = discord.Embed(
            title="👥 Sélectionner des rôles",
            description="Ajoutez des rôles éligibles ou ignorés pour cette configuration.",
            color=discord.Color.purple()
        )
        select = Select(
            placeholder="Choisissez un rôle",
            options=[
                discord.SelectOption(label=role.name, value=str(role.id))
                for role in interaction.guild.roles
            ]
        )

        async def select_callback(interaction: discord.Interaction):
            role_id = int(select.values[0])
            await interaction.response.send_message(f"Rôle sélectionné : <@&{role_id}>", ephemeral=True)
            # Étape suivante : Confirmer la configuration
            await self.confirm_configuration(interaction, action, channel_id, role_id)

        select.callback = select_callback
        view = View()
        view.add_item(select)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def confirm_configuration(self, interaction: discord.Interaction, action: str, channel_id: int, role_id: int):
        """Affiche un résumé de la configuration et demande une confirmation."""
        embed = discord.Embed(
            title="✅ Confirmer la configuration",
            description="Voici un résumé de la configuration que vous avez créée :",
            color=discord.Color.green()
        )
        embed.add_field(name="Action", value=action, inline=False)
        embed.add_field(name="Salon", value=f"<#{channel_id}>", inline=False)
        embed.add_field(name="Rôle", value=f"<@&{role_id}>", inline=False)
        embed.set_footer(text="Cliquez sur Confirmer pour enregistrer ou Annuler pour abandonner.")

        view = View()

        # Bouton pour confirmer
        confirm_button = Button(label="Confirmer", style=discord.ButtonStyle.green)
        async def confirm_callback(interaction: discord.Interaction):
            self.save_configuration(interaction.guild.id, action, channel_id, role_id)
            self.cog.save_configurations()
            await interaction.response.send_message("✅ Configuration enregistrée avec succès !", ephemeral=True)
        confirm_button.callback = confirm_callback
        view.add_item(confirm_button)

        # Bouton pour annuler
        cancel_button = Button(label="Annuler", style=discord.ButtonStyle.red)
        async def cancel_callback(interaction: discord.Interaction):
            await interaction.response.send_message("❌ Configuration annulée.", ephemeral=True)
        cancel_button.callback = cancel_callback
        view.add_item(cancel_button)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    def save_configuration(self, guild_id: int, action: str, channel_id: int, role_id: int):
        """Enregistre la configuration dans le stockage."""
        if guild_id not in self.cog.configurations:
            self.cog.configurations[guild_id] = []
        self.cog.configurations[guild_id].append({
            "action": action,
            "channel_id": channel_id,
            "role_id": role_id
        })

    @discord.ui.button(label="Modifier une configuration", style=discord.ButtonStyle.blurple)
    async def modify_config(self, interaction: discord.Interaction, button: Button):
        """Modifie une configuration existante."""
        guild_id = interaction.guild.id
        if guild_id not in self.cog.configurations or not self.cog.configurations[guild_id]:
            await interaction.response.send_message("❌ Aucune configuration existante à modifier.", ephemeral=True)
            return

        embed = discord.Embed(
            title="⚙️ Modifier une configuration",
            description="Sélectionnez une configuration à modifier.",
            color=discord.Color.blurple()
        )
        options = [
            discord.SelectOption(
                label=f"Action: {config['action']} | Salon: <#{config['channel_id']}> | Rôle: <@&{config['role_id']}>",
                value=str(index)
            )
            for index, config in enumerate(self.cog.configurations[guild_id])
        ]
        select = Select(placeholder="Choisissez une configuration", options=options)

        async def select_callback(interaction: discord.Interaction):
            config_index = int(select.values[0])
            config = self.cog.configurations[guild_id][config_index]
            await interaction.response.send_message(
                f"Configuration sélectionnée : Action: {config['action']}, Salon: <#{config['channel_id']}>, Rôle: <@&{config['role_id']}>",
                ephemeral=True
            )
            # Relancer le processus de modification (action, salon, rôle)
            await self.add_condition(interaction)

        select.callback = select_callback
        view = View()
        view.add_item(select)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Supprimer une configuration", style=discord.ButtonStyle.red)
    async def delete_config(self, interaction: discord.Interaction, button: Button):
        """Supprime une configuration existante."""
        guild_id = interaction.guild.id
        if guild_id not in self.cog.configurations or not self.cog.configurations[guild_id]:
            await interaction.response.send_message("❌ Aucune configuration existante à supprimer.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🗑️ Supprimer une configuration",
            description="Sélectionnez une configuration à supprimer.",
            color=discord.Color.red()
        )
        options = [
            discord.SelectOption(
                label=f"Action: {config['action']} | Salon: <#{config['channel_id']}> | Rôle: <@&{config['role_id']}>",
                value=str(index)
            )
            for index, config in enumerate(self.cog.configurations[guild_id])
        ]
        select = Select(placeholder="Choisissez une configuration..", options=options)

        async def select_callback(interaction: discord.Interaction):
            config_index = int(select.values[0])
            removed_config = self.cog.configurations[guild_id].pop(config_index)
            self.cog.save_configurations()
            await interaction.response.send_message(
                f"✅ Configuration supprimée : Action: {removed_config['action']}, Salon: <#{removed_config['channel_id']}>, Rôle: <@&{removed_config['role_id']}>",
                ephemeral=True
            )

        select.callback = select_callback
        view = View()
        view.add_item(select)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ConfigEvent(bot))