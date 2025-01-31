import discord
from discord.ext import commands
from discord import app_commands

class Utilitaire(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

# FAKE COMMAND -----------------------------

    @discord.app_commands.hybrid_command(name="fake", description="Affiche un membre comme étant fake")
    @commands.guild_only()
    async def fake(self, ctx, member: discord.Member):
        """Renomme le membre spécifié en fake (ajoute [fake] avant son pseudo) et annonce dans un salon"""
        
        new_nick = f"[fake] {member.display_name}"

        try:
            await member.edit(nick=new_nick)
            await ctx.send(f"{member.mention} a été affiché comme fake !.")
        except discord.Forbidden:
            await ctx.send(f"Je n'ai pas les permissions nécessaires pour renommer {member.name}.")
            return

        salon_id = 1250466390675292201
        channel = self.bot.get_channel(salon_id)
        if channel:
            await channel.send(f"{member.mention} est considéré comme fake par le staff, attention aux interactions avec cette personne.")
        else:
            await ctx.send("Le salon d'annonce n'a pas été trouvé.")

# EFFACER COMMAND -----------------------------

    @discord.app_commands.hybrid_command(name="effacer", description="Efface un nombre spécifié de messages")
    @commands.has_permissions(manage_messages=True)
    async def effacer(self, ctx, nombre: int):
        """Efface un nombre spécifié de messages"""
        
        # Vérifie que le nombre de messages à supprimer est dans la plage valide
        if nombre < 1 or nombre > 100:
            await ctx.send("Tu peux supprimer entre 1 et 100 messages à la fois.")
            return

        # Efface les messages
        deleted = await ctx.channel.purge(limit=nombre)
        await ctx.send(f"{len(deleted)} messages ont été supprimés.", delete_after=5)


def setup(bot):
    bot.add_cog(Utilitaire(bot))