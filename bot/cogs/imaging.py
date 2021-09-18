import discordSuperUtils
from discord.ext import commands

from bot.constants import welcome_channel_id, member_role_id


class Imaging(commands.Cog, discordSuperUtils.CogManager.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.ImageManager = discordSuperUtils.ImageManager()
        super().__init__()

    @commands.Cog.listener()
    async def on_member_join(self, guild, member):
        channel = guild.get_channel(welcome_channel_id)
        member_role = guild.get_role(member_role_id)

        await member.add_roles(member_role)

        await channel.send(
            file=await self.ImageManager.create_welcome_card(
                member,
                discordSuperUtils.Backgrounds.GAMING,
                (255, 255, 255),
                f"Welcome, {member} 🔥",
                "Welcome to discordSuperUtils, Please read the #rules.",
                transparency=127,
            )
        )


def setup(bot):
    bot.add_cog(Imaging(bot))
