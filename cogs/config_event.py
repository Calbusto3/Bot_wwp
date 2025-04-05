import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput, Select
import json
import os
import uuid

def generate_config_id():
    return str(uuid.uuid4())[:6]

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
        return {
            "guild_id": {
                "abc123": {
                    "role_id": 1234567890,
                    "type": "gain",
                    "action": "send_message",
                    "message": "Bienvenue !",
                    "channel_id": 456,
                    "enabled": True
                },
                "def456": {
                    "role_id": 9876543210,
                    "type": "perte",
                    "action": "send_emoji",
                    "emoji": "😢",
                    "channel_id": 789,
                    "enabled": True
                }
            }
        }

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
        embed.add_field(name="➕ Ajouter une règle", value="Ajoutez une nouvelle règle conditionnelle.", inline=False)
        embed.add_field(name="📝 Modifier une règle", value="Modifiez une règle existante.", inline=False)
        embed.add_field(name="🗑️ Supprimer une règle", value="Supprimez une règle existante.", inline=False)
        embed.add_field(name="✅/❌ Activer/Désactiver", value="Activez ou désactivez une règle.", inline=False)
        embed.add_field(name="🧾 Voir les règles", value="Affichez toutes les règles configurées.", inline=False)

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

    async def execute_action(self, guild_id: int, action: str, channel_id: int, member: discord.Member, message: str = None, emoji: str = None):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            print(f"❌ Guild introuvable : {guild_id}")
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            print(f"❌ Salon introuvable : {channel_id}")
            return

        print(f"✅ Exécution de l'action '{action}' pour le membre {member.name} dans le salon {channel.name}")
        if action == "send_message" and message:
            await channel.send(f"{member.mention}, {message}")
        elif action == "send_emoji" and emoji:
            await channel.send(emoji)
        elif action == "react_message":
            async for msg in channel.history(limit=1):
                await msg.add_reaction(emoji or "👍")

    async def handle_role_event(self, member: discord.Member, role: discord.Role, event_type: str):
        guild_id = str(member.guild.id)
        configs = self.configurations.get(guild_id, {})

        for config_id, rule in configs.items():
            # Filtrer les règles par rôle et type d'événement
            if rule["role_id"] == role.id and rule["type"] == event_type and rule["enabled"]:
                await self.execute_action(
                    guild_id=member.guild.id,
                    action=rule["action"],
                    channel_id=rule["channel_id"],
                    member=member,
                    message=rule.get("message"),
                    emoji=rule.get("emoji")
                )

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        before_roles = set(before.roles)
        after_roles = set(after.roles)

        lost_roles = before_roles - after_roles
        gained_roles = after_roles - before_roles

        guild_id = str(after.guild.id)
        if guild_id not in self.configurations:
            return

        # Gérer les rôles gagnés
        for role in gained_roles:
            await self.handle_role_event(member=after, role=role, event_type="gain")

        # Gérer les rôles perdus
        for role in lost_roles:
            await self.handle_role_event(member=after, role=role, event_type="perte")

class EditConfigModal(Modal, title="✏️ Modifier la configuration"):
    def __init__(self, cog: ConfigEvent, guild_id: str, index: int, config: dict):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id
        self.index = index

        # Menu déroulant pour les actions prédéfinies
        self.action = Select(
            placeholder="Choisissez une action...",
            options=[
                discord.SelectOption(label="Envoyer un message", value="send_message"),
                discord.SelectOption(label="Envoyer un fichier", value="send_file"),
                discord.SelectOption(label="Envoyer un emoji", value="send_emoji"),
                discord.SelectOption(label="Réagir à un message", value="react_message"),
            ]
        )
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
        if self.action.values[0] not in valid_actions:
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
            "action": self.action.values[0],
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

class AddRuleModal(Modal, title="➕ Ajouter une règle"):
    def __init__(self, cog):
        super().__init__()
        self.cog = cog

        self.trigger_role = TextInput(label="ID du rôle déclencheur", placeholder="123456789012345678", required=True)
        self.event_type = Select(
            placeholder="Type d'événement...",
            options=[
                discord.SelectOption(label="Gain de rôle", value="gain"),
                discord.SelectOption(label="Perte de rôle", value="perte"),
            ]
        )
        self.action = Select(
            placeholder="Choisissez une action...",
            options=[
                discord.SelectOption(label="Envoyer un message", value="send_message"),
                discord.SelectOption(label="Envoyer un emoji", value="send_emoji"),
                discord.SelectOption(label="Réagir à un message", value="react_message"),
            ]
        )
        self.channel_id = TextInput(label="ID du salon cible", placeholder="123456789012345678", required=True)
        self.message = TextInput(label="Message (si applicable)", placeholder="Bienvenue !", required=False)

        self.add_item(self.trigger_role)
        self.add_item(self.event_type)
        self.add_item(self.action)
        self.add_item(self.channel_id)
        self.add_item(self.message)

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        config_id = generate_config_id()

        # Sauvegarde de la règle
        self.cog.configurations.setdefault(guild_id, {})[config_id] = {
            "role_id": int(self.trigger_role.value.strip()),
            "type": self.event_type.values[0],
            "action": self.action.values[0],
            "channel_id": int(self.channel_id.value.strip()),
            "message": self.message.value.strip() if self.message.value else None,
            "enabled": True
        }
        self.cog.save_configurations()

        await interaction.response.send_message(f"✅ Nouvelle règle ajoutée avec succès (ID : `{config_id}`) !", ephemeral=True)

class ConfigEventView(View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog
        self.add_item(Button(label="Ajouter une condition", style=discord.ButtonStyle.green, custom_id="config_event_add_condition", row=0))
        self.add_item(Button(label="Modifier une configuration", style=discord.ButtonStyle.blurple, custom_id="config_event_modify_config", row=1))
        self.add_item(Button(label="Supprimer une configuration", style=discord.ButtonStyle.red, custom_id="config_event_delete_config", row=2))
        self.add_item(Button(label="Voir les configurations", style=discord.ButtonStyle.gray, custom_id="config_event_view_configs", row=3))

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

        options = [
            discord.SelectOption(label=f"Règle #{i+1}: {config['action']}", value=str(i))
            for i, config in enumerate(configs)
        ]
        select = discord.ui.Select(placeholder="Sélectionnez une configuration", options=options)

        async def select_callback(interaction: discord.Interaction):
            selected_index = int(select.values[0])
            config = configs[selected_index]
            modal = EditConfigModal(self.cog, guild_id, selected_index, config)
            await interaction.response.send_modal(modal)

        select.callback = select_callback
        view = View()
        view.add_item(select)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

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

            # Boutons avec callbacks
            button_confirm = Button(label="Confirmer", style=discord.ButtonStyle.red)
            button_cancel = Button(label="Annuler", style=discord.ButtonStyle.green)

            async def confirm_callback(i: discord.Interaction):
                del self.cog.configurations[guild_id][selected_index]
                self.cog.save_configurations()
                await i.response.send_message("✅ Configuration supprimée avec succès.", ephemeral=True)

            async def cancel_callback(i: discord.Interaction):
                await i.response.send_message("❌ Suppression annulée.", ephemeral=True)

            button_confirm.callback = confirm_callback
            button_cancel.callback = cancel_callback

            confirmation_view.add_item(button_confirm)
            confirmation_view.add_item(button_cancel)

            await interaction.response.send_message(embed=confirmation_embed, view=confirmation_view, ephemeral=True)

    @discord.ui.button(label="Modifier une règle", style=discord.ButtonStyle.blurple)
    async def modify_rule(self, interaction: discord.Interaction, button: Button):
        guild_id = str(interaction.guild.id)
        configs = self.cog.configurations.get(guild_id, {})

        if not configs:
            await interaction.response.send_message("📭 Aucune règle à modifier.", ephemeral=True)
            return

        options = [
            discord.SelectOption(label=f"Règle `{config_id}`", value=config_id)
            for config_id in configs
        ]
        select = discord.ui.Select(placeholder="Choisissez une règle à modifier", options=options)

        async def select_callback(interaction: discord.Interaction):
            selected_id = select.values[0]
            config = configs[selected_id]
            modal = EditConfigModal(self.cog, guild_id, selected_id, config)
            await interaction.response.send_modal(modal)

        select.callback = select_callback
        view = View()
        view.add_item(select)
        await interaction.response.send_message("Sélectionnez une règle à modifier :", view=view, ephemeral=True)

    @discord.ui.button(label="Voir les règles", style=discord.ButtonStyle.gray)
    async def view_rules(self, interaction: discord.Interaction, button: Button):
        guild_id = str(interaction.guild.id)
        configs = self.cog.configurations.get(guild_id, {})

        if not configs:
            await interaction.response.send_message("📭 Aucune règle configurée pour ce serveur.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📋 Règles configurées",
            description="Voici la liste des règles actuelles :",
            color=discord.Color.gold()
        )
        for config_id, config in configs.items():
            embed.add_field(
                name=f"🟢 Règle `{config_id}`",
                value=f"**Type** : {config['type'].capitalize()}\n"
                      f"**Déclencheur** : <@&{config['role_id']}>\n"
                      f"**Action** : `{config['action']}`\n"
                      f"**Salon** : <#{config['channel_id']}>\n"
                      f"**Statut** : {'✅ Activée' if config['enabled'] else '❌ Désactivée'}",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Activer/Désactiver", style=discord.ButtonStyle.green)
    async def toggle_rule(self, interaction: discord.Interaction, button: Button):
        guild_id = str(interaction.guild.id)
        configs = self.cog.configurations.get(guild_id, {})

        if not configs:
            await interaction.response.send_message("📭 Aucune règle à activer/désactiver.", ephemeral=True)
            return

        options = [
            discord.SelectOption(label=f"Règle `{config_id}`", value=config_id)
            for config_id in configs
        ]
        select = discord.ui.Select(placeholder="Choisissez une règle à activer/désactiver", options=options)

        async def select_callback(interaction: discord.Interaction):
            selected_id = select.values[0]
            config = configs[selected_id]
            config["enabled"] = not config["enabled"]
            self.cog.save_configurations()
            await interaction.response.send_message(f"✅ Règle `{selected_id}` {'activée' if config["enabled"] else 'désactivée'} avec succès.", ephemeral=True)

        select.callback = select_callback
        view = View()
        view.add_item(select)
        await interaction.response.send_message("Sélectionnez une règle à activer/désactiver :", view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ConfigEvent(bot))
