import discord
from discord.ext import commands
from discord import app_commands
import json
import os

class Utilitaire(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.permissions_file = "role_permissions.json"
        self.role_permissions = self.load_permissions()

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

# ROLE COMMAND --------------------------------

    def load_permissions(self):
        """Charge les permissions depuis le fichier JSON."""
        if os.path.exists(self.permissions_file):
            with open(self.permissions_file, "r") as f:
                return json.load(f)
        return {}

    def save_permissions(self):
        """Sauvegarde les permissions dans le fichier JSON."""
        with open(self.permissions_file, "w") as f:
            json.dump(self.role_permissions, f, indent=4)

    @commands.has_permissions(administrator=True)
    @app_commands.command(name="roleperm", description="Permet à un rôle de donner et retirer un autre rôle.")
    async def set_role_permission(self, ctx: discord.Interaction, executant_role: discord.Role, target_role: discord.Role):
        if str(executant_role.id) not in self.role_permissions:
            self.role_permissions[str(executant_role.id)] = []

        if target_role.id not in self.role_permissions[str(executant_role.id)]:
            self.role_permissions[str(executant_role.id)].append(target_role.id)
            self.save_permissions()
            await ctx.response.send_message(
                f"Le rôle `{executant_role.name}` peut désormais attribuer et retirer le rôle `{target_role.name}`.", ephemeral=True
            )
        else:
            await ctx.response.send_message(
                f"Le rôle `{executant_role.name}` peut déjà gérer `{target_role.name}`.", ephemeral=True
            )

    @commands.has_permissions(administrator=True)
    @app_commands.command(name="roleperm_remove", description="Retire la permission d'un rôle d'en gérer un autre.")
    async def remove_role_permission(self, ctx: discord.Interaction, executant_role: discord.Role, target_role: discord.Role):
        if str(executant_role.id) not in self.role_permissions or target_role.id not in self.role_permissions[str(executant_role.id)]:
            await ctx.response.send_message(
                f"Le rôle `{executant_role.name}` ne peut déjà pas gérer `{target_role.name}`.", ephemeral=True
            )
            return

        self.role_permissions[str(executant_role.id)].remove(target_role.id)
        if not self.role_permissions[str(executant_role.id)]:
            del self.role_permissions[str(executant_role.id)]  # Nettoyage si la liste est vide

        self.save_permissions()
        await ctx.response.send_message(
            f"Le rôle `{executant_role.name}` ne peut désormais plus gérer `{target_role.name}`.", ephemeral=True
        )

    @app_commands.command(name="roleadd", description="Ajoute un rôle à un membre.")
    async def add_role(self, ctx: discord.Interaction, member: discord.Member, role: discord.Role):
        author_roles = [role.id for role in ctx.user.roles]

        authorized = any(str(role_id) in self.role_permissions and role.id in self.role_permissions[str(role_id)] for role_id in author_roles)

        if not authorized:
            await ctx.response.send_message("Tu n'as pas la permission de donner ce rôle.", ephemeral=True)
            return

        try:
            await member.add_roles(role)
            await ctx.response.send_message(f"Le rôle `{role.name}` a été attribué à {member.mention}.")
        except discord.Forbidden:
            await ctx.response.send_message("Je n'ai pas les permissions nécessaires pour attribuer ce rôle.", ephemeral=True)

    @app_commands.command(name="roleremove", description="Retire un rôle d'un membre.")
    async def remove_role(self, ctx: discord.Interaction, member: discord.Member, role: discord.Role):
        author_roles = [role.id for role in ctx.user.roles]

        authorized = any(str(role_id) in self.role_permissions and role.id in self.role_permissions[str(role_id)] for role_id in author_roles)

        if not authorized:
            await ctx.response.send_message("Tu n'as pas la permission de retirer ce rôle.", ephemeral=True)
            return

        try:
            await member.remove_roles(role)
            await ctx.response.send_message(f"Le rôle `{role.name}` a été retiré de {member.mention}.")
        except discord.Forbidden:
            await ctx.response.send_message("Je n'ai pas les permissions nécessaires pour retirer ce rôle.", ephemeral=True)

def setup(bot):
    bot.add_cog(Utilitaire(bot))