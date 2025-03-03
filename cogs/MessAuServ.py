import discord
from discord.ext import commands
from discord.ui import Button, View
from discord import ButtonStyle, Interaction

class MessageAll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="message_all", description="Envoyer un message à tout le monde dans le serveur.")
    @commands.has_permissions(administrator=True)
    async def message_all(self, ctx, title: str, content: str, footer: str, color: str = "#3498db"):
        """Envoi un message à tous les membres du serveur avec un embed et des boutons."""
        
        # Création de l'embed
        embed = self.create_embed(title, content, footer, color)

        # Création des boutons
        buttons = self.create_buttons(ctx, embed)

        # Envoi de la prévisualisation
        preview_msg = await ctx.send(
            embed=embed,
            content="**Prévisualisation** : ajustez avant l'envoi :",
            view=buttons,
            ephemeral=True
        )

        # Sauvegarde des données nécessaires pour les callbacks
        buttons.preview_msg = preview_msg
        buttons.embed = embed

    def create_embed(self, title: str, content: str, footer: str, color: str):
        """Crée un embed Discord avec les paramètres fournis."""
        try:
            embed_color = int(color.strip("#"), 16)
        except ValueError:
            embed_color = 0x3498db  # Défaut si couleur invalide
        embed = discord.Embed(title=title, description=content, color=embed_color)
        embed.set_footer(text=footer)
        return embed

    def create_buttons(self, ctx, embed):
        """Crée et configure les boutons d'interaction."""
        buttons = View(timeout=300)  # Timeout de 5 minutes

        confirm_button = Button(label="Confirmer", style=ButtonStyle.green)
        cancel_button = Button(label="Annuler", style=ButtonStyle.red)
        edit_button = Button(label="Modifier", style=ButtonStyle.blurple)
        color_button = Button(label="Changer la couleur", style=ButtonStyle.grey)

        # Callbacks pour chaque bouton
        async def confirm_callback(interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ Vous ne pouvez pas confirmer cette action.", ephemeral=True)
                return
            failed_members = await self.send_to_all_members(ctx.guild, embed)
            await interaction.response.edit_message(content=f"✅ Message envoyé avec succès.\n{failed_members} membres inaccessibles.", view=None)

        async def cancel_callback(interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ Vous ne pouvez pas annuler cette action.", ephemeral=True)
                return
            await interaction.response.edit_message(content="❌ Envoi annulé.", view=None)

        async def edit_callback(interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ Vous ne pouvez pas modifier ce message.", ephemeral=True)
                return
            await self.handle_edit(interaction, embed)

        async def color_callback(interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ Vous ne pouvez pas modifier ce message.", ephemeral=True)
                return
            await self.handle_color_change(interaction, embed)

        # Associer les callbacks
        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback
        edit_button.callback = edit_callback
        color_button.callback = color_callback

        # Ajouter les boutons à la vue
        buttons.add_item(confirm_button)
        buttons.add_item(cancel_button)
        buttons.add_item(edit_button)
        buttons.add_item(color_button)

        return buttons

    async def send_to_all_members(self, guild, embed):
        """Envoie le message à tous les membres du serveur."""
        failed_members = []
        for member in guild.members:
            if not member.bot:
                try:
                    await member.send(embed=embed)
                except discord.Forbidden:
                    continue
                except Exception:
                    failed_members.append(str(member))
        return len(failed_members)

    async def handle_edit(self, interaction, embed):
        """Permet à l'utilisateur de modifier les champs de l'embed."""
        await interaction.response.send_message("📝 Entrez les champs à modifier (`titre`, `contenu`, `footer`).", ephemeral=True)

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        msg = await self.bot.wait_for('message', check=check)
        fields_to_edit = msg.content.split()
        for field in fields_to_edit:
            if field == "titre":
                await interaction.followup.send("Entrez le nouveau titre :", ephemeral=True)
                title_msg = await self.bot.wait_for('message', check=check)
                embed.title = title_msg.content
            elif field == "contenu":
                await interaction.followup.send("Entrez le nouveau contenu :", ephemeral=True)
                content_msg = await self.bot.wait_for('message', check=check)
                embed.description = content_msg.content
            elif field == "footer":
                await interaction.followup.send("Entrez le nouveau footer :", ephemeral=True)
                footer_msg = await self.bot.wait_for('message', check=check)
                embed.set_footer(text=footer_msg.content)
        await interaction.edit_original_response(embed=embed)

    async def handle_color_change(self, interaction, embed):
        """Permet à l'utilisateur de changer la couleur de l'embed."""
        await interaction.response.send_message("🎨 Entrez une nouvelle couleur en hexadécimal.", ephemeral=True)

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        color_msg = await self.bot.wait_for('message', check=check)
        try:
            embed.color = int(color_msg.content.strip("#"), 16)
            await interaction.edit_original_response(embed=embed)
        except ValueError:
            await interaction.followup.send("❌ Couleur invalide.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MessageAll(bot))