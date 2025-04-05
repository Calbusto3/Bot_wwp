import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
import json
import os

class ConfigEvent(commands.Cog):
    CONFIG_FILE = "configurations.json"

    def __init__(self, bot):
        self.bot = bot
        self.configurations = self.load_configurations()

    def save_configurations(self):
        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.configurations, f, indent=4)

    def load_configurations(self):
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_configuration(self, guild_id, action, channel_id, trigger_role, eligible_roles, ignored_roles):
        if guild_id not in self.configurations:
            self.configurations[guild_id] = []
        self.configurations[guild_id].append({
            "action": action,
            "channel_id": channel_id,
            "trigger_role": trigger_role,
            "eligible_roles": eligible_roles,
            "ignored_roles": ignored_roles
        })
        self.save_configurations()

    def update_configuration(self, guild_id, index, updated_config):
        self.configurations[guild_id][index] = updated_config
        self.save_configurations()

    @app_commands.command(name="config_event", description="Configurer des événements conditionnels.")
    @app_commands.default_permissions(administrator=True)
    async def config_event(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚙️ Configuration des événements",
            description="Utilisez les boutons ci-dessous pour gérer les configurations.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Ajouter une condition", value="Ajoutez une nouvelle condition à un événement.", inline=False)
        embed.add_field(name="Modifier une configuration", value="Modifiez une configuration existante.", inline=False)
        embed.add_field(name="Supprimer une configuration", value="Supprimez une configuration existante.", inline=False)
        embed.add_field(name="Voir les configurations", value="Consultez toutes les règles configurées.", inline=False)

        view = ConfigEventView(self)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="list_config", description="Liste toutes les configurations existantes.")
    @app_commands.default_permissions(administrator=True)
    async def list_config(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        configs = self.configurations.get(guild_id, [])

        if not configs:
            await interaction.response.send_message("❌ Aucune configuration existante.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📋 Configurations existantes",
            description="Voici la liste des configurations actuelles :",
            color=discord.Color.blue()
        )
        for index, config in enumerate(configs):
            embed.add_field(
                name=f"Configuration {index + 1}",
                value=f"**Action**: {config['action']}\n"
                      f"**Salon**: <#{config['channel_id']}>\n"
                      f"**Rôles éligibles**: {', '.join(f'<@&{role}>' for role in config['eligible_roles'])}\n"
                      f"**Rôles ignorés**: {', '.join(f'<@&{role}>' for role in config['ignored_roles'])}",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def execute_action(self, guild_id: int, action: str, channel_id: int, member: discord.Member):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            print(f"❌ Guild introuvable : {guild_id}")
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            print(f"❌ Salon introuvable : {channel_id}")
            return

        print(f"✅ Exécution de l'action '{action}' pour le membre {member.name} dans le salon {channel.name}")
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
        if before.roles == after.roles:
            return

        added_roles = [role for role in after.roles if role not in before.roles]
        added_role_ids = [role.id for role in added_roles]
        current_role_ids = [role.id for role in after.roles]

        guild_id = str(after.guild.id)
        if guild_id not in self.configurations:
            return

        for config in self.configurations[guild_id]:
            trigger_role = config.get("trigger_role")
            eligible_roles = config.get("eligible_roles", [])
            ignored_roles = config.get("ignored_roles", [])

            if trigger_role not in added_role_ids:
                continue

            if eligible_roles and not any(rid in current_role_ids for rid in eligible_roles):
                continue

            if any(rid in current_role_ids for rid in ignored_roles):
                continue

            await self.execute_action(
                guild_id=after.guild.id,
                action=config["action"],
                channel_id=config["channel_id"],
                member=after
            )

class EditConfigModal(Modal, title="✏️ Modifier la configuration"):
    def __init__(self, cog: ConfigEvent, guild_id: str, index: int, config: dict):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id
        self.index = index

        # Menu déroulant pour les actions prédéfinies
        self.action = TextInput(label="Action", default=config.get("action", ""), required=True)
        self.channel_id = TextInput(label="ID du salon", default=str(config.get("channel_id", "")), required=True)
        self.trigger_role = TextInput(label="ID du rôle déclencheur", default=str(config.get("trigger_role", "")), required=True)
        self.eligible_roles = TextInput(label="Rôles éligibles (IDs séparés par des virgules)", default=",".join(map(str, config.get("eligible_roles", []))), required=False)
        self.ignored_roles = TextInput(label="Rôles ignorés (IDs séparés par des virgules)", default=",".join(map(str, config.get("ignored_roles", []))), required=False)

        self.add_item(self.action)
        self.add_item(self.channel_id)
        self.add_item(self.trigger_role)
        self.add_item(self.eligible_roles)
        self.add_item(self.ignored_roles)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild

        # Validation de l'action
        valid_actions = ["send_message", "send_file", "send_emoji", "react_message"]
        if self.action.value.strip() not in valid_actions:
            await interaction.response.send_message("❌ Action invalide. Choisissez parmi : send_message, send_file, send_emoji, react_message.", ephemeral=True)
            return

        # Vérification du salon
        channel = guild.get_channel(int(self.channel_id.value.strip()))
        if not channel:
            await interaction.response.send_message("❌ Le salon spécifié est introuvable.", ephemeral=True)
            return

        # Vérification des rôles
        eligible_roles = [guild.get_role(int(r.strip())) for r in self.eligible_roles.value.split(",") if r.strip()]
        ignored_roles = [guild.get_role(int(r.strip())) for r in self.ignored_roles.value.split(",") if r.strip()]
        if not all(eligible_roles) or not all(ignored_roles):
            await interaction.response.send_message("❌ Un ou plusieurs rôles spécifiés sont introuvables.", ephemeral=True)
            return

        # Gestion de l'ajout ou de la modification
        updated_config = {
            "action": self.action.value.strip(),
            "channel_id": int(self.channel_id.value.strip()),
            "trigger_role": int(self.trigger_role.value.strip()),
            "eligible_roles": [role.id for role in eligible_roles],
            "ignored_roles": [role.id for role in ignored_roles]
        }
        if self.index == -1:
            self.cog.save_configuration(self.guild_id, **updated_config)
        else:
            self.cog.update_configuration(self.guild_id, self.index, updated_config)

        embed = discord.Embed(
            title="✅ Configuration ajoutée/modifiée",
            color=discord.Color.green(),
            description=f"**Action** : `{updated_config['action']}`\n"
                        f"**Déclencheur** : <@&{updated_config['trigger_role']}>\n"
                        f"**Salon** : <#{updated_config['channel_id']}>\n"
                        f"**Éligibles** : {', '.join(f'<@&{r}>' for r in updated_config['eligible_roles']) or 'Aucun'}\n"
                        f"**Ignorés** : {', '.join(f'<@&{r}>' for r in updated_config['ignored_roles']) or 'Aucun'}"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ConfigEventView(View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog
        self.add_item(Button(label="Ajouter une condition", style=discord.ButtonStyle.green, custom_id="add_condition", row=0))
        self.add_item(Button(label="Modifier une configuration", style=discord.ButtonStyle.blurple, custom_id="modify_config", row=1))
        self.add_item(Button(label="Supprimer une configuration", style=discord.ButtonStyle.red, custom_id="delete_config", row=2))
        self.add_item(Button(label="Voir les configurations", style=discord.ButtonStyle.gray, custom_id="view_configs", row=3))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Vous devez être administrateur pour utiliser cette commande.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Ajouter une condition", style=discord.ButtonStyle.green)
    async def add_condition(self, interaction: discord.Interaction, button: Button):
        """Ajoute une nouvelle condition via une modale."""
        modal = EditConfigModal(self.cog, str(interaction.guild.id), -1, {})
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Voir les configurations", style=discord.ButtonStyle.gray, custom_id="view_configs")
    async def view_configurations(self, interaction: discord.Interaction, button: Button):
        guild_id = str(interaction.guild.id)
        configs = self.cog.configurations.get(guild_id, [])

        if not configs:
            await interaction.response.send_message("📭 Aucune configuration trouvée pour ce serveur.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📋 Configurations existantes",
            description=f"Total : {len(configs)} configurations",
            color=discord.Color.gold()
        )

        for i, config in enumerate(configs, start=1):
            eligible = ", ".join(f"<@&{rid}>" for rid in config.get("eligible_roles", []))
            ignored = ", ".join(f"<@&{rid}>" for rid in config.get("ignored_roles", []))
            embed.add_field(
                name=f"🔹 Règle #{i}",
                value=(
                    f"**Action** : `{config.get('action')}`\n"
                    f"**Déclencheur** : <@&{config.get('trigger_role')}>\n"
                    f"**Salon** : <#{config.get('channel_id')}>\n"
                    f"**Éligibles** : {eligible or 'Aucun'}\n"
                    f"**Ignorés** : {ignored or 'Aucun'}\n"
                    f"\n➡️ Cliquez pour modifier cette configuration."
                ),
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        async def button_callback(interaction: discord.Interaction):
            index = 0  # à récupérer dynamiquement si on a plusieurs boutons plus tard
            config = configs[index]
            modal = EditConfigModal(self.cog, guild_id, index, config)
            await interaction.response.send_modal(modal)

    @discord.ui.button(label="Supprimer une configuration", style=discord.ButtonStyle.red, custom_id="delete_config")
    async def delete_configuration(self, interaction: discord.Interaction, button: Button):
        guild_id = str(interaction.guild.id)
        configs = self.cog.configurations.get(guild_id, [])

        if not configs:
            await interaction.response.send_message("❌ Aucune configuration à supprimer.", ephemeral=True)
            return

        # Création d'un sélecteur pour la suppression
        options = [
            discord.SelectOption(label=f"Règle #{i+1}: {config['action']}", value=str(i))
            for i, config in enumerate(configs)
        ]
        select = discord.ui.Select(placeholder="Sélectionnez une configuration à supprimer", options=options)

        async def select_callback(interaction: discord.Interaction):
            selected_index = int(select.values[0])
            config_to_delete = configs[selected_index]

            # Demander une confirmation avant suppression
            confirmation_embed = discord.Embed(
                title="❌ Confirmation de suppression",
                description=f"Êtes-vous sûr de vouloir supprimer la configuration suivante :\n\n"
                            f"**Action** : `{config_to_delete['action']}`\n"
                            f"**Déclencheur** : <@&{config_to_delete['trigger_role']}>\n"
                            f"**Salon** : <#{config_to_delete['channel_id']}>\n"
                            f"**Éligibles** : {', '.join(f'<@&{r}>' for r in config_to_delete['eligible_roles']) or 'Aucun'}\n"
                            f"**Ignorés** : {', '.join(f'<@&{r}>' for r in config_to_delete['ignored_roles']) or 'Aucun'}",
                color=discord.Color.red()
            )
            confirmation_view = View()
            confirmation_view.add_item(Button(label="Confirmer", style=discord.ButtonStyle.red, custom_id="confirm_delete", row=0))
            confirmation_view.add_item(Button(label="Annuler", style=discord.ButtonStyle.green, custom_id="cancel_delete", row=1))

            confirmation_view.get_item_by_id("confirm_delete").callback = lambda i: self.confirm_delete(i, guild_id, selected_index)
            confirmation_view.get_item_by_id("cancel_delete").callback = self.cancel_delete

            await interaction.response.send_message(embed=confirmation_embed, view=confirmation_view, ephemeral=True)

        async def confirm_delete(self, interaction: discord.Interaction, guild_id: str, selected_index: int):
            del self.cog.configurations[guild_id][selected_index]
            self.cog.save_configurations()
            await interaction.response.send_message("✅ Configuration supprimée avec succès.", ephemeral=True)

        async def cancel_delete(self, interaction: discord.Interaction):
            await interaction.response.send_message("❌ Suppression annulée.", ephemeral=True)

        select.callback = select_callback
        await interaction.response.send_message("Sélectionnez une configuration à supprimer.", view=View(select), ephemeral=True)

async def setup(bot):
    await bot.add_cog(ConfigEvent(bot))
