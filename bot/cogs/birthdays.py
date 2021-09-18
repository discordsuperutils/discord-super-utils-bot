from datetime import datetime, timezone

import aiosqlite
import discord
import discordSuperUtils
import pytz
from discord.ext import commands

from bot.constants import birthday_channel_id


def ordinal(num: int) -> str:
    """
    Returns the ordinal representation of a number

    Examples:
        11: 11th
        13: 13th
        14: 14th
        3: 3rd
        5: 5th

    :param num:
    :return:
    """

    return (
        f"{num}th"
        if 11 <= (num % 100) <= 13
        else f"{num}{['th', 'st', 'nd', 'rd', 'th'][min(num % 10, 4)]}"
    )


class Birthday(commands.Cog, discordSuperUtils.CogManager.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.BirthdayManager = discordSuperUtils.BirthdayManager(bot)
        super().__init__()

    @discordSuperUtils.CogManager.event(discordSuperUtils.BirthdayManager)
    async def on_member_birthday(self, birthday_member):
        # Not gonna make a system as the bot isnt going to be used outside of our support server
        channel = birthday_member.member.guild.get_channel(birthday_channel_id)

        if channel:
            embed = discord.Embed(
                title="Happy birthday!",
                description=f"Happy {ordinal(await birthday_member.age() + 1)} birthday, {birthday_member.member.mention}!",
                color=0x00FF00,
            )  # TODO: change to raw on release

            embed.set_thumbnail(url=birthday_member.member.avatar_url)

            await channel.send(content=birthday_member.member.mention, embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        database = discordSuperUtils.DatabaseManager.connect(
            await aiosqlite.connect("main.sqlite")
        )
        await self.BirthdayManager.connect_to_database(database, ["birthdays"])

    @commands.command()
    async def upcoming(self, ctx):
        guild_upcoming = await self.BirthdayManager.get_upcoming(ctx.guild)
        formatted_upcoming = [
            f"Member: {x.member}, Age: {await x.age()}, Date of Birth: {(await x.birthday_date()):'%b %d %Y'}"
            for x in guild_upcoming
        ]

        await discordSuperUtils.PageManager(
            ctx,
            discordSuperUtils.generate_embeds(
                formatted_upcoming,
                title="Upcoming Birthdays",
                fields=25,
                description=f"Upcoming birthdays in {ctx.guild}",
            ),
        ).run()

    @commands.command()
    async def birthday(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        member_birthday = await self.BirthdayManager.get_birthday(member)

        if not member_birthday:
            await ctx.send("The specified member does not have a birthday setup!")
            return

        embed = discord.Embed(title=f"{member}'s Birthday", color=0x00FF00)

        embed.add_field(
            name="Birthday",
            value=(await member_birthday.birthday_date()).strftime("%b %d %Y"),
            inline=False,
        )

        embed.add_field(
            name="Timezone", value=await member_birthday.timezone(), inline=False
        )

        embed.add_field(
            name="Age", value=str(await member_birthday.age()), inline=False
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def setup_birthday(self, ctx):
        questions = [
            "What year where you born in?",
            "What month where you born in?",
            "What day of month where you born in?",
            "What is your timezone? List: https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568"
            "\nAlternatively, you can use the timezone picker: "
            "http://scratch.andrewl.in/timezone-picker/example_site/openlayers_example.html",
        ]

        answers, timed_out = await discordSuperUtils.questionnaire(
            ctx, questions, member=ctx.author
        )
        # The questionnaire supports embeds.

        if timed_out:
            await ctx.send("You have timed out.")
            return

        for answer in answers[:-1]:
            if not answer.isnumeric():
                await ctx.send("Setup failed.")
                return

            i = answers.index(answer)
            answers[i] = int(answer)

        if answers[3] not in pytz.all_timezones:
            await ctx.send("Setup failed, timezone not found.")
            return

        try:
            now = datetime.now(tz=timezone.utc)
            date_of_birth = datetime(*answers[:-1], tzinfo=timezone.utc)
            if date_of_birth > now:
                await ctx.send("Setup failed, your date of birth is in the future.")
                return
        except ValueError:
            await ctx.send("Setup failed.")
            return

        member_birthday = await self.BirthdayManager.get_birthday(ctx.author)
        if member_birthday:
            await member_birthday.set_birthday_date(date_of_birth.timestamp())
            await member_birthday.set_timezone(answers[3])
        else:
            await self.BirthdayManager.create_birthday(
                ctx.author, date_of_birth.timestamp(), answers[3]
            )

        await ctx.send(f"Successfully set your birthday to {date_of_birth:%b %d %Y}.")


def setup(bot):
    bot.add_cog(Birthday(bot))
