import discord
from discord.ext import commands

class WelcomeMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_message_1 = """🔥 **Le Meilleur Site de Rencontres 18+ ! **🔥

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
"""  # Message de bienvenue personnalisé pour le serveur 18+

        self.welcome_message_2 = """Nous vous mettons un serveur à disponibilité dans lequel nous **donnerons gratuitement** aux membres des jeux (**sensé être payant**) régulièrement.

- Pour y entrer, faire une **candidature** dans le serveur, soyez convainquant : 
> https://discord.gg/mwsYspWkzF

Des questions ? -> ⁠<#1141835303573799065>
"""  # Deuxième message

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Envoie un message de bienvenue en DM à chaque nouveau membre, puis envoie un second message."""
        try:
            # Envoi du premier message de bienvenue
            await member.send(self.welcome_message_1)
            
            # Envoi du deuxième message
            await member.send(self.welcome_message_2)
        except discord.Forbidden:
            # Si l'option d'envoi de DM est désactivée, on prévient dans la console
            print(f"Impossible d'envoyer un message à {member.name} en DM.")

async def setup(bot):
    await bot.add_cog(WelcomeMessage(bot))