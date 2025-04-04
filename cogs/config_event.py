import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select
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

    def save_configuration(self, guild_id, action, channel_id, role_id1, role_id2, role_id3):
        """Ajoute une nouvelle configuration et la sauvegarde."""
        if guild_id not in self.configurations:
            self.configurations[guild_id] = []
        self.configurations[guild_id].append({
            "action": action,
            "channel_id": channel_id,
            "eligible_roles": [role_id1, role_id2],
            "ignored_roles": [role_id3]
        })
        self.save_configurations()

    @app_commands.command(name="config_event", description="Configurer des événements conditionnels.")
    @app_commands.default_permissions(administrator=True)
    async def config_event(self, interaction: discord.Interaction):
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
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)  # Réponse directe

    async def execute_action(self, guild_id: int, action: str, channel_id: int, role_id: int, member: discord.Member, error_channel: discord.TextChannel):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            await error_channel.send(f"⚠️ Le salon configuré (<#{channel_id}>) n'existe plus.")
            return

        role = guild.get_role(role_id)
        if not role:
            await error_channel.send(f"⚠️ Le rôle configuré (<@&{role_id}>) n'existe plus.")
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
                eligible_roles = config.get("eligible_roles", [])
                ignored_roles = config.get("ignored_roles", [])

                if eligible_roles and not any(role.id in eligible_roles for role in after.roles):
                    return  # Le membre n'a pas de rôle éligible

                if any(role.id in ignored_roles for role in after.roles):
                    return  # Le membre a un rôle ignoré

                if config["role_id"] in [role.id for role in added_roles]:
                    await self.execute_action(
                        guild_id=guild_id,
                        action=config["action"],
                        channel_id=config["channel_id"],
                        role_id=config["role_id"],
                        member=after,
                        error_channel=after.guild.system_channel  # Exemple : salon système
                    )

class ConfigEventView(View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

        # Bouton pour ajouter une condition
        self.add_item(Button(label="Ajouter une condition", style=discord.ButtonStyle.green, custom_id="add_condition", row=0))

        # Bouton pour modifier une configuration
        self.add_item(Button(label="Modifier une configuration", style=discord.ButtonStyle.blurple, custom_id="modify_config", row=1))

        # Bouton pour supprimer une configuration
        self.add_item(Button(label="Supprimer une configuration", style=discord.ButtonStyle.red, custom_id="delete_config", row=2))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Vérifie si l'utilisateur est administrateur."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Vous devez être administrateur pour utiliser cette commande.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Ajouter une condition", style=discord.ButtonStyle.green)
    async def add_condition(self, interaction: discord.Interaction, button: Button):
        """Ajoute une nouvelle condition."""
        await interaction.response.defer(ephemeral=True)  # Diffère la réponse
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
        view = View()
        view.add_item(select)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)  # Utilisez followup.send

    async def select_channel(self, interaction: discord.Interaction, action: str):
        """Permet de sélectionner un salon pour l'action."""
        await interaction.response.defer(ephemeral=True)
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
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="👥 Sélectionner des rôles",
            description="Ajoutez des rôles éligibles ou ignorés pour cette configuration.",
            color=discord.Color.purple()
        )
        select = Select(
            placeholder="Choisissez des rôles (éligibles ou ignorés)",
            options=[
                discord.SelectOption(label=role.name, value=str(role.id))
                for role in interaction.guild.roles
            ],
            min_values=1,
            max_values=len(interaction.guild.roles)
        )

        async def select_callback(interaction: discord.Interaction):
            selected_roles = [int(role_id) for role_id in select.values]
            eligible_roles = selected_roles[:-1]  # Tous sauf le dernier rôle
            ignored_roles = selected_roles[-1:]  # Dernier rôle comme ignoré
            await interaction.response.send_message(
                f"Rôles sélectionnés : {', '.join(f'<@&{role_id}>' for role_id in eligible_roles)} (éligibles), "
                f"{', '.join(f'<@&{role_id}>' for role_id in ignored_roles)} (ignorés)",
                ephemeral=True
            )
            # Étape suivante : Confirmer la configuration
            await self.confirm_configuration(interaction, action, channel_id, eligible_roles, ignored_roles)

        select.callback = select_callback
        view = View()
        view.add_item(select)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    async def confirm_configuration(self, interaction: discord.Interaction, action: str, channel_id: int, role_id1: int, role_id2: int, role_id3: int):
        """Affiche un résumé de la configuration et demande une confirmation."""
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="✅ Confirmer la configuration",
            description="Voici un résumé de la configuration que vous avez créée :",
            color=discord.Color.green()
        )
        embed.add_field(name="Action", value=action, inline=False)
        embed.add_field(name="Salon", value=f"<#{channel_id}>", inline=False)
        embed.add_field(name="Rôles éligibles", value=f"<@&{role_id1}>, <@&{role_id2}>", inline=False)
        embed.add_field(name="Rôles ignorés", value=f"<@&{role_id3}>", inline=False)
        embed.set_footer(text="Cliquez sur Confirmer pour enregistrer ou Annuler pour abandonner.")

        view = View()

        # Bouton pour confirmer
        confirm_button = Button(label="Confirmer", style=discord.ButtonStyle.green)
        async def confirm_callback(interaction: discord.Interaction):
            self.cog.save_configuration(interaction.guild.id, action, channel_id, role_id1, role_id2, role_id3)
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

async def setup(bot):
    await bot.add_cog(ConfigEvent(bot))