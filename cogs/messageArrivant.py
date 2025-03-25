import discord
import json
from discord.ext import commands
from discord.ui import Button, View
from discord import ButtonStyle, Interaction


class SetupAccueil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "welcome_messages.json"
        self.load_config()

    def load_config(self):
        """Charge la configuration des messages d'accueil."""
        try:
            with open(self.config_file, "r", encoding="utf-8") as file:
                self.config = json.load(file)
        except FileNotFoundError:
            self.config = {"active": False, "messages": []}
            self.save_config()

    def save_config(self):
        """Sauvegarde la configuration."""
        with open(self.config_file, "w", encoding="utf-8") as file:
            json.dump(self.config, file, indent=4)

    @commands.hybrid_command(name="setup_accueil", description="Configurer les messages d'accueil.")
    @commands.has_permissions(administrator=True)
    async def setup_accueil(self, ctx):
        """Affiche l'interface de configuration des messages d'accueil."""
        view = self.create_view()
        embed = self.create_embed()
        await ctx.send(embed=embed, view=view)

    def create_embed(self):
        """Crée l'embed de configuration."""
        status = "✅ **Activé**" if self.config["active"] else "❌ **Désactivé**"
        messages = "\n".join(f"**{i+1}.** {msg}" for i, msg in enumerate(self.config["messages"]))
        messages = messages if messages else "Aucun message défini."
        
        embed = discord.Embed(title="Configuration des messages d'accueil", color=discord.Color.blue())
        embed.add_field(name="Statut", value=status, inline=False)
        embed.add_field(name="Messages définis", value=messages, inline=False)
        embed.set_footer(text="Utilisez les boutons ci-dessous pour gérer les messages.")
        return embed

    def create_view(self):
        """Crée la vue avec les boutons d'interaction."""
        view = View(timeout=300)
        
        toggle_button = Button(label="Activé" if self.config["active"] else "Désactivé",
                               style=ButtonStyle.green if self.config["active"] else ButtonStyle.grey)
        
        add_button = Button(label="Ajouter", style=ButtonStyle.blurple)
        edit_button = Button(label="Modifier", style=ButtonStyle.blurple)
        delete_button = Button(label="Supprimer", style=ButtonStyle.red)
        
        async def toggle_callback(interaction):
            self.config["active"] = not self.config["active"]
            self.save_config()
            view = self.create_view()
            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=view)

        async def add_callback(interaction):
            await interaction.response.send_message("✏️ Entrez le message d'accueil à ajouter :", ephemeral=True)
            def check(msg): return msg.author == interaction.user and msg.channel == interaction.channel
            msg = await self.bot.wait_for("message", check=check)
            self.config["messages"].append(msg.content)
            self.save_config()
            await interaction.followup.send("✅ Message ajouté !", ephemeral=True)

        async def edit_callback(interaction):
            if not self.config["messages"]:
                await interaction.response.send_message("⚠️ Aucun message à modifier.", ephemeral=True)
                return
            
            await interaction.response.send_message("🔢 Entrez le numéro du message à modifier :", ephemeral=True)
            def check(msg): return msg.author == interaction.user and msg.channel == interaction.channel
            num_msg = await self.bot.wait_for("message", check=check)
            
            try:
                index = int(num_msg.content) - 1
                if index < 0 or index >= len(self.config["messages"]):
                    raise ValueError
            except ValueError:
                await interaction.followup.send("❌ Numéro invalide.", ephemeral=True)
                return
            
            await interaction.followup.send("✏️ Entrez le nouveau message :", ephemeral=True)
            new_msg = await self.bot.wait_for("message", check=check)
            self.config["messages"][index] = new_msg.content
            self.save_config()
            await interaction.followup.send("✅ Message modifié !", ephemeral=True)

        async def delete_callback(interaction):
            if not self.config["messages"]:
                await interaction.response.send_message("⚠️ Aucun message à supprimer.", ephemeral=True)
                return
            
            await interaction.response.send_message("🔢 Entrez le numéro du message à supprimer :", ephemeral=True)
            def check(msg): return msg.author == interaction.user and msg.channel == interaction.channel
            num_msg = await self.bot.wait_for("message", check=check)
            
            try:
                index = int(num_msg.content) - 1
                if index < 0 or index >= len(self.config["messages"]):
                    raise ValueError
            except ValueError:
                await interaction.followup.send("❌ Numéro invalide.", ephemeral=True)
                return
            
            del self.config["messages"][index]
            self.save_config()
            await interaction.followup.send("✅ Message supprimé !", ephemeral=True)

        toggle_button.callback = toggle_callback
        add_button.callback = add_callback
        edit_button.callback = edit_callback
        delete_button.callback = delete_callback

        view.add_item(toggle_button)
        view.add_item(add_button)
        view.add_item(edit_button)
        view.add_item(delete_button)
        
        return view

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Envoie les messages d'accueil aux nouveaux membres si activé."""
        if self.config["active"] and self.config["messages"]:
            for msg in self.config["messages"]:
                try:
                    await member.send(msg)
                except discord.Forbidden:
                    break

async def setup(bot):
    await bot.add_cog(SetupAccueil(bot))