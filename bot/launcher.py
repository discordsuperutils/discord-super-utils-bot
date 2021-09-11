from bot.core.bot import DiscordSuperUtilsBot
import json


def load_token(file: str) -> str:
    """
    Loads the bot token from a JSON file.

    :param file: The JSON file.
    :type file: str
    :return: str
    :rtype: str
    """

    with open(file) as f:
        return json.load(f)["token"]


def main():
    bot = DiscordSuperUtilsBot(load_token("config.json"), command_prefix=".")
    bot.run()


if __name__ == "__main__":
    main()
