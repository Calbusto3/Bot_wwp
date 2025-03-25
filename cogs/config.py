import discord
from discord.ext import commands
from discord.ui import Select, View, Button

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="config", description="Configurer les fonctionnalités du bot.")
    @commands.has_permissions(administrator=True)
    async def config(self, ctx, option: str = None):
        """Commande principale pour configurer les fonctionnalités du bot."""
        
        if option is None:
            embed = self.create_main_embed()
            view = self.create_main_view()
            await ctx.send(embed=embed, view=view)
        elif option.lower() == "setup_accueil":
            # Ici, on appelle directement la configuration de l'accueil
            cog = self.bot.get_cog("SetupAccueil")
            if cog:
                await cog.setup_accueil(ctx)
            else:
                await ctx.send("⚠️ Le module de configuration d'accueil est introuvable.")

    def create_main_embed(self):
        """Crée l'embed principal du menu de configuration."""
        embed = discord.Embed(title="⚙️ Configuration du bot",
                              description="Sélectionnez une fonctionnalité à configurer",
                              color=discord.Color.blue())
        embed.add_field(name="📌 Options disponibles :",
                        value="- `Setup Accueil` : Configurer les messages d'accueil.\n- *(Autres à venir...)*",
                        inline=False)
        embed.set_footer(text="Utilisez le menu déroulant ci-dessous pour choisir.")
        return embed

    def create_main_view(self):
        """Crée la vue avec le menu déroulant pour choisir une configuration."""
        view = View()
        
        select = Select(
            placeholder="Choisissez une fonctionnalité à configurer...",
            options=[
                discord.SelectOption(label="Setup Accueil", value="setup_accueil", description="Configurer les messages d'accueil.")
            ]
        )
        
        async def select_callback(interaction):
            await interaction.response.defer()
            option = select.values[0]
            ctx = await self.bot.get_context(interaction.message)
            await self.config(ctx, option)
        
        select.callback = select_callback
        view.add_item(select)
        return view

async def setup(bot):
    await bot.add_cog(Config(bot))