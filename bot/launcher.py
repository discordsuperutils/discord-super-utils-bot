from constants import token

import discord
import discordSuperUtils

from bot.core.bot import DiscordSuperUtilsBot


def main():
    bot = DiscordSuperUtilsBot(token, command_prefix=".", intents=discord.Intents.all())
    discordSuperUtils.CommandHinter(bot)
    bot.run()


if __name__ == "__main__":
    main()
