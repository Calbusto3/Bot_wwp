import discord
import json
from discord.ext import commands
from discord.ui import Button, View, Select
from discord import ButtonStyle, Interaction

class SetupAccueil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "welcome_messages.json"
        self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, "r", encoding="utf-8") as file:
                self.config = json.load(file)
        except FileNotFoundError:
            self.config = {"active": False, "messages": {}}
            self.save_config()

    def save_config(self):
        with open(self.config_file, "w", encoding="utf-8") as file:
            json.dump(self.config, file, indent=4)

    @commands.hybrid_command(name="setup_accueil", description="Configurer les messages d'accueil.")
    @commands.has_permissions(administrator=True)
    async def setup_accueil(self, ctx):
        view = self.create_view()
        embed = self.create_embed()
        await ctx.send(embed=embed, view=view)

    def create_embed(self):
        status = "✅ **Activé**" if self.config["active"] else "❌ **Désactivé**"
        messages = "\n".join(f"**{title}**" for title in self.config["messages"]) if self.config["messages"] else "Aucun message défini."
        
        embed = discord.Embed(title="Configuration des messages d'accueil", color=discord.Color.blue())
        embed.add_field(name="Statut", value=status, inline=False)
        embed.add_field(name="Messages définis", value=messages, inline=False)
        embed.set_footer(text="Utilisez les boutons et le menu ci-dessous pour gérer les messages.")
        return embed

    def create_view(self):
        view = View(timeout=300)

        toggle_button = Button(label="Activé" if self.config["active"] else "Désactivé",
                               style=ButtonStyle.green if self.config["active"] else ButtonStyle.grey)
        add_button = Button(label="Ajouter", style=ButtonStyle.blurple)
        delete_button = Button(label="Supprimer", style=ButtonStyle.red)
        select_menu = Select(placeholder="Sélectionner un message", options=[
            discord.SelectOption(label=title, value=title) for title in self.config["messages"]
        ]) if self.config["messages"] else None

        async def toggle_callback(interaction):
            self.config["active"] = not self.config["active"]
            self.save_config()
            await interaction.response.edit_message(embed=self.create_embed(), view=self.create_view())

        async def add_callback(interaction):
            await interaction.response.send_message("✏️ Entrez le titre du message :", ephemeral=True)
            def check(msg): return msg.author == interaction.user and msg.channel == interaction.channel
            title_msg = await self.bot.wait_for("message", check=check)
            title = title_msg.content.strip()
            if title in self.config["messages"]:
                await interaction.followup.send("⚠️ Un message avec ce titre existe déjà.", ephemeral=True)
                return
            await interaction.followup.send("✏️ Entrez le contenu du message :", ephemeral=True)
            content_msg = await self.bot.wait_for("message", check=check)
            self.config["messages"][title] = content_msg.content
            self.save_config()
            await interaction.followup.send("✅ Message ajouté !", ephemeral=True)
            await interaction.message.edit(embed=self.create_embed(), view=self.create_view())

        async def delete_callback(interaction):
            if not self.config["messages"]:
                await interaction.response.send_message("⚠️ Aucun message à supprimer.", ephemeral=True)
                return
            await interaction.response.send_message("🔢 Entrez le titre du message à supprimer :", ephemeral=True)
            def check(msg): return msg.author == interaction.user and msg.channel == interaction.channel
            title_msg = await self.bot.wait_for("message", check=check)
            title = title_msg.content.strip()
            if title not in self.config["messages"]:
                await interaction.followup.send("❌ Titre introuvable.", ephemeral=True)
                return
            del self.config["messages"][title]
            self.save_config()
            await interaction.followup.send("✅ Message supprimé !", ephemeral=True)
            await interaction.message.edit(embed=self.create_embed(), view=self.create_view())

        async def select_callback(interaction):
            title = interaction.data["values"][0]
            message = self.config["messages"].get(title, "Message introuvable.")
            await interaction.response.send_message(f"**{title}**\n{message}", ephemeral=True)

        toggle_button.callback = toggle_callback
        add_button.callback = add_callback
        delete_button.callback = delete_callback

        view.add_item(toggle_button)
        view.add_item(add_button)
        view.add_item(delete_button)
        if select_menu:
            select_menu.callback = select_callback
            view.add_item(select_menu)

        return view

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if self.config["active"] and self.config["messages"]:
            for message in self.config["messages"].values():
                try:
                    await member.send(message)
                except discord.Forbidden:
                    break

async def setup(bot):
    await bot.add_cog(SetupAccueil(bot))
