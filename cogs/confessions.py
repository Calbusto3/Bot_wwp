import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput, Select
import json
import os

class ConfessView(discord.ui.View):
    def __init__(self, confession_embed, confession_id, bot):
        super().__init__(timeout=None)
        self.confession_embed = confession_embed
        self.confession_id = confession_id
        self.bot = bot

    @discord.ui.button(label="Répondre", style=discord.ButtonStyle.primary, emoji="💬")
    async def respond_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        thread = await interaction.channel.create_thread(
            name=f"Discussion Confession #{self.confession_id}",
            message=interaction.message,
            auto_archive_duration=60,
            reason="Réponse à une confession"
        )
        await thread.send("**N'oubliez pas d'utiliser `/confesser` pour répondre anonymement !**")
        await interaction.response.send_message(f"Fil créé : {thread.mention} ✅", ephemeral=True)

    @discord.ui.button(label="Signaler", style=discord.ButtonStyle.danger, emoji="🚨")
    async def report_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ReportModal(self.confession_id, self.bot)
        await interaction.response.send_modal(modal)

class ReportModal(discord.ui.Modal, title="Signaler une confession"):
    def __init__(self, confession_id, bot):
        super().__init__()
        self.confession_id = confession_id
        self.bot = bot

        self.reason = discord.ui.TextInput(label="Raison (ex: pédophilie)", placeholder="Entrez un mot clé", max_length=100)
        self.details = discord.ui.TextInput(label="Détails", style=discord.TextStyle.paragraph, placeholder="Expliquez en détail votre signalement...", max_length=1000)

        self.add_item(self.reason)
        self.add_item(self.details)

    async def on_submit(self, interaction: discord.Interaction):
        logs_channel = interaction.client.get_channel(1250220762489552956)

        embed = discord.Embed(title=f"🚨 Signalement - Confession #{self.confession_id}", color=discord.Color.red())
        embed.add_field(name="Raison", value=self.reason.value, inline=False)
        embed.add_field(name="Détails", value=self.details.value, inline=False)
        embed.add_field(name="Signalé par", value=interaction.user.mention, inline=False)

        await logs_channel.send(embed=embed)
        await interaction.response.send_message("Merci pour votre signalement ! Le Staff l'a bien reçus✅", ephemeral=True)

class Confesser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.confession_count = self.load_confession_count()
        self.cooldowns = {}  # Utilisateur : dernier timestamp

    def load_confession_count(self):
        if not os.path.exists("confession_count.json"):
            with open("confession_count.json", "w") as f:
                json.dump({"count": 0}, f)
        with open("confession_count.json", "r") as f:
            data = json.load(f)
            return data["count"]

    def save_confession_count(self):
        with open("confession_count.json", "w") as f:
            json.dump({"count": self.confession_count}, f)

    @app_commands.command(name="confesser", description="Confessez vos acts anonymement.")
    async def confesser(self, interaction: discord.Interaction, *, confession: str):
        # Anti message trop court
        if len(confession.strip()) < 10:
            await interaction.response.send_message("Votre confession est trop courte. Minimum **10 caractères** requis !", ephemeral=True)
            return

        # Cooldown
        now = discord.utils.utcnow().timestamp()
        last_time = self.cooldowns.get(interaction.user.id, 0)

        staff_role = 1134290681490317403
        booster_role = 1133157563098218586

        cooldown = 10  # Membre normal

        if any(role.id == staff_role for role in interaction.user.roles):
            cooldown = 0  # Staff = pas de cooldown
        elif any(role.id == booster_role for role in interaction.user.roles):
            cooldown = 5  # Booster = 5 secondes

        if cooldown > 0 and now - last_time < cooldown:
            remaining = int(cooldown - (now - last_time))
            await interaction.response.send_message(f"⏳ Vous devez attendre encore {remaining} secondes avant de confesser à nouveau.", ephemeral=True)
            return

        self.cooldowns[interaction.user.id] = now

        # Envoyer la confession
        self.confession_count += 1
        self.save_confession_count()

        confession_embed = discord.Embed(
            title=f"🕯️ Confession #{self.confession_count}",
            description=confession,
            color=discord.Color.purple()
        )

        await interaction.channel.send(embed=confession_embed, view=ConfessView(confession_embed, self.confession_count, self.bot))

        # Logs pour le staff
        logs_channel = interaction.client.get_channel(1250220762489552956)
        staff_embed = discord.Embed(title=f"🕵️ Confession #{self.confession_count} (Log)", color=discord.Color.blurple())
        staff_embed.add_field(name="Confession", value=confession, inline=False)
        staff_embed.add_field(name="Membre", value=f"{interaction.user.mention} ({interaction.user.name}#{interaction.user.discriminator} / ID: {interaction.user.id})", inline=False)
        staff_embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await logs_channel.send(embed=staff_embed)
        await interaction.response.send_message("Votre confession a été envoyée anonymement. ✅", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Confesser(bot))
