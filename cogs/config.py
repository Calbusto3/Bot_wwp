import discord
from discord.ext import commands
from discord.ui import Select, View

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="config", description="Configurer les fonctionnalités du bot.")
    @commands.has_permissions(administrator=True)
    async def config(self, ctx, option: str = None):
        """Commande principale pour configurer les fonctionnalités du bot."""
        
        if option is None:
            embed = self.create_main_embed()
            view = self.create_main_view(ctx)
            await ctx.send(embed=embed, view=view)
        elif option.lower() == "setup_accueil":
            cog = self.bot.get_cog("SetupAccueil")
            if cog:
                await cog.run_setup_accueil(ctx)  # Appel mis à jour
            else:
                await ctx.send("⚠️ Le module de configuration d'accueil est introuvable.")
        elif option.lower() == "setup_autorole":
            cog = self.bot.get_cog("AutoRole")
            if cog:
                await cog.setup_auto_role(ctx.interaction)  # Correction de l'appel
            else:
                await ctx.send("⚠️ Le module de configuration des autorôles est introuvable.")

    def create_main_embed(self):
        """Crée l'embed principal du menu de configuration."""
        embed = discord.Embed(
            title="⚙️ Configuration du bot",
            description="Sélectionnez une fonctionnalité à configurer",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📌 Options disponibles :",
            value="- `Setup Accueil` : Configurer les messages d'accueil.\n- `Setup Autorôle` : Configurer les autorôles.",
            inline=False
        )
        embed.set_footer(text="Utilisez le menu déroulant ci-dessous pour choisir.")
        return embed

    def create_main_view(self, ctx):
        """Crée la vue avec le menu déroulant pour choisir une configuration."""
        view = View()
        
        select = Select(
            placeholder="Choisissez une fonctionnalité à configurer...",
            options=[
                discord.SelectOption(label="Setup Accueil", value="setup_accueil", description="Configurer les messages d'accueil."),
                discord.SelectOption(label="Setup Autorôle", value="setup_autorole", description="Configurer les autorôles.")
            ]
        )
        
        async def select_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            option = select.values[0]
            await self.config(ctx, option)
        
        select.callback = select_callback
        view.add_item(select)
        return view

async def setup(bot):
    await bot.add_cog(Config(bot))