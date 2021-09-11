from __future__ import annotations

from discord.ext import commands
import logging
import os

__all__ = ("DiscordSuperUtilsBot",)


class DiscordSuperUtilsBot(commands.Bot):
    """
    Represents a DiscordSuperUtilsBot.
    """

    __slots__ = ("token",)

    def __init__(self, token: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = token

    async def on_ready(self):
        print(f"{self.user} is ready.")

    def load_cogs(self, directory: str) -> None:
        """
        Loads all the cogs in the directory.

        :param directory: The directory
        :type directory: str
        :return: None
        :rtype: None
        """

        for file in os.listdir(directory):
            if not file.endswith(".py") or file.startswith("__"):
                continue

            try:
                self.load_extension(f'{directory}.{file.replace(".py", "")}')
                logging.info(f"Loaded cog {file}")
            except Exception as e:
                logging.critical(f"An exception has been raised when loading cog {file}")
                raise e

    def run(self) -> None:
        """
        Runs the bot.

        :return: None
        :rtype: None
        """

        self.load_cogs("cogs")
        self.loop.run_until_complete(super().start(self.token, bot=True))
        self.loop.run_forever()
