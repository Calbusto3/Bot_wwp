import discord
from discord.ext import commands

class WelcomeMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_message = """🔥 **Le Meilleur Site de Rencontres 18+ ! **🔥

🔞 Vous cherchez des rencontres torrides sans limites ?
Rejoignez une communauté où de vrais adultes sont prêts à discuter, flirter et s’amuser !

✅ De vraies personnes, aucun bot
💬 Chat ouvert & messages privés
💥 Contenu exclusif
❤️ Trouvez votre match parfait en toute simplicité

🔗 **Rejoignez-nous maintenant : [CLIQUEZ ICI](https://go.trklinkcm.com/aff_nl?offer_id=10000&aff_id=61260&lands=133&aff_sub=abigadi&aff_sub5=free-social&source=mb)**
🔗 **Rejoignez-nous maintenant : [CLIQUEZ ICI](https://go.trklinkcm.com/aff_nl?offer_id=10000&aff_id=61260&lands=133&aff_sub=abigadi&aff_sub5=free-social&source=mb)**
🔗 **Rejoignez-nous maintenant : [CLIQUEZ ICI](https://go.trklinkcm.com/aff_nl?offer_id=10000&aff_id=61260&lands=133&aff_sub=abigadi&aff_sub5=free-social&source=mb)**

Strictement réservé aux 18+ !
"""  # Message personnalisé pour le serveur 18+

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Envoie un message de bienvenue en DM à chaque nouveau membre."""
        try:
            # Envoi du message en DM
            await member.send(self.welcome_message)
        except discord.Forbidden:
            # Si l'option d'envoi de DM est désactivée, on prévient dans la console
            print(f"Impossible d'envoyer un message à {member.name} en DM.")

async def setup(bot):
    await bot.add_cog(WelcomeMessage(bot))