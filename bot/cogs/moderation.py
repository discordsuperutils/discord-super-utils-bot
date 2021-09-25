from datetime import datetime

import aiosqlite
import discord
import discordSuperUtils
from discord.ext import commands


async def make_removed_embeds(removed_infractions, member):
    return discordSuperUtils.generate_embeds(
        [
            f"**Reason: **{infraction.reason}\n"
            f"**ID: **{infraction.infraction_id}\n"
            f"**Date of Infraction: **{infraction.date_of_infraction}"
            for infraction in removed_infractions
        ],
        title=f"Removed Infractions",
        fields=25,
        description=f"List of infractions that were removed from {member.mention}.",
    )


async def make_infraction_embed(member_infractions, member):
    return discordSuperUtils.generate_embeds(
        [
            f"**Reason: **{await infraction.reason()}\n"
            f"**ID: **{infraction.infraction_id}\n"
            f"**Date of Infraction: **{await infraction.datetime()}"
            for infraction in member_infractions
        ],
        title=f"Infractions of {member}",
        fields=25,
        description=f"List of {member.mention}'s infractions.",
    )


class Moderation(commands.Cog, discordSuperUtils.CogManager.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.InfractionManager = discordSuperUtils.InfractionManager(bot)
        self.MuteManager = discordSuperUtils.MuteManager(bot)
        self.BanManager = discordSuperUtils.BanManager(bot)

        self.InfractionManager.add_punishments(
            [
                discordSuperUtils.Punishment(
                    punishment_manager=self.MuteManager,
                    punishment_reason="Crossed 3 infractions.",
                ),
                discordSuperUtils.Punishment(
                    punishment_manager=self.BanManager,
                    punishment_reason="Crossed 5 infractions.",
                    punish_after=5,
                ),
            ]
        )
        super().__init__()

    @discordSuperUtils.CogManager.event(discordSuperUtils.MuteManager)
    @discordSuperUtils.CogManager.event(discordSuperUtils.BanManager)
    async def on_punishment(self, ctx, member, punishment):
        await ctx.send(f"{member.mention} has been punished!")

    @discordSuperUtils.CogManager.event(discordSuperUtils.MuteManager)
    async def on_unmute(self, member, reason):
        print(f"{member} has been unmuted. Mute reason: {reason}")

    @discordSuperUtils.CogManager.event(discordSuperUtils.BanManager)
    async def on_unban(self, member, reason):
        print(f"{member} has been unbanned. Ban reason: {reason}")

    @commands.Cog.listener()
    async def on_ready(self):
        database = discordSuperUtils.DatabaseManager.connect(
            await aiosqlite.connect("main.sqlite")
        )

        await self.InfractionManager.connect_to_database(database, ["infractions"])
        await self.BanManager.connect_to_database(database, ["bans"])
        await self.MuteManager.connect_to_database(database, ["mutes"])

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def mute(
        self,
        ctx,
        member: discord.Member,
        time_of_mute: discordSuperUtils.TimeConvertor,
        reason: str = "No reason specified.",
    ):
        try:
            await self.MuteManager.mute(member, reason, time_of_mute)
        except discordSuperUtils.AlreadyMuted:
            await ctx.send(f"{member} is already muted.")
        else:
            await ctx.send(f"{member} has been muted. Reason: {reason}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unmute(self, ctx, member: discord.Member):
        if await self.MuteManager.unmute(member):
            await ctx.send(f"{member.mention} has been unmuted.")
        else:
            await ctx.send(f"{member.mention} is not muted!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ban(
        self,
        ctx,
        member: discord.Member,
        time_of_ban: discordSuperUtils.TimeConvertor,
        reason: str = "No reason specified.",
    ):
        await ctx.send(f"{member} has been banned. Reason: {reason}")
        await self.BanManager.ban(member, reason, time_of_ban)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unban(self, ctx, user: discord.User):
        if await self.BanManager.unban(user, guild=ctx.guild):
            await ctx.send(f"{user} has been unbanned.")
        else:
            await ctx.send(f"{user} is not banned.")

    @commands.group(invoke_without_command=True)
    async def infractions(self, ctx, member: discord.Member):
        member_infractions = await self.InfractionManager.get_infractions(member)

        await discordSuperUtils.PageManager(
            ctx,
            await make_infraction_embed(member_infractions, member),
        ).run()

    @infractions.command()
    @commands.has_permissions(administrator=True)
    async def add(
        self, ctx, member: discord.Member, reason: str = "No reason specified."
    ):
        infraction = await self.InfractionManager.warn(ctx, member, reason)

        embed = discord.Embed(title=f"{member} has been warned.", color=0x00FF00)

        embed.add_field(name="Reason", value=await infraction.reason(), inline=False)
        embed.add_field(
            name="Infraction ID", value=infraction.infraction_id, inline=False
        )
        embed.add_field(
            name="Date of Infraction",
            value=str(await infraction.datetime()),
            inline=False,
        )

        await ctx.send(embed=embed)

    @infractions.command()
    async def get(self, ctx, member: discord.Member, infraction_id: str):
        infractions_found = await self.InfractionManager.get_infractions(
            member, infraction_id=infraction_id
        )

        if not infractions_found:
            await ctx.send(
                f"Cannot find infraction with id {infraction_id} on {member.mention}'s account"
            )
            return

        infraction = infractions_found[0]

        embed = discord.Embed(
            title=f"Infraction found on {member}'s account!", color=0x00FF00
        )

        embed.add_field(name="Reason", value=await infraction.reason(), inline=False)
        embed.add_field(
            name="Infraction ID", value=infraction.infraction_id, inline=False
        )
        embed.add_field(
            name="Date of Infraction",
            value=str(await infraction.datetime()),
            inline=False,
        )
        # Incase you don't like the Date of Infraction format you can change it using datetime.strftime

        await ctx.send(embed=embed)

    @infractions.command()
    async def get_before(
        self, ctx, member: discord.Member, from_time: discordSuperUtils.TimeConvertor
    ):
        from_timestamp = datetime.utcnow().timestamp() - from_time

        member_infractions = await self.InfractionManager.get_infractions(
            member, from_timestamp=from_timestamp
        )

        await discordSuperUtils.PageManager(
            ctx,
            await make_infraction_embed(member_infractions, member),
        ).run()

    @infractions.command()
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx, member: discord.Member):
        removed_infractions = []

        for infraction in await self.InfractionManager.get_infractions(member):
            removed_infractions.append(await infraction.delete())

        await discordSuperUtils.PageManager(
            ctx,
            await make_removed_embeds(removed_infractions, member),
        ).run()

    @infractions.command()
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx, member: discord.Member, infraction_id: str):
        infractions_found = await self.InfractionManager.get_infractions(
            member, infraction_id=infraction_id
        )

        if not infractions_found:
            await ctx.send(
                f"Cannot find infraction with id {infraction_id} on {member.mention}'s account"
            )
            return

        removed_infraction = await infractions_found[0].delete()

        embed = discord.Embed(
            title=f"Infraction removed from {member}'s account!", color=0x00FF00
        )

        embed.add_field(name="Reason", value=removed_infraction.reason, inline=False)
        embed.add_field(
            name="Infraction ID", value=removed_infraction.infraction_id, inline=False
        )
        embed.add_field(
            name="Date of Infraction",
            value=str(removed_infraction.date_of_infraction),
            inline=False,
        )

        await ctx.send(embed=embed)

    @infractions.command()
    @commands.has_permissions(administrator=True)
    async def remove_before(
        self, ctx, member: discord.Member, from_time: discordSuperUtils.TimeConvertor
    ):
        from_timestamp = datetime.utcnow().timestamp() - from_time

        member_infractions = await self.InfractionManager.get_infractions(
            member, from_timestamp=from_timestamp
        )
        removed_infractions = []

        for infraction in member_infractions:
            removed_infractions.append(await infraction.delete())

        await discordSuperUtils.PageManager(
            ctx,
            await make_removed_embeds(removed_infractions, member),
        ).run()


def setup(bot):
    bot.add_cog(Moderation(bot))
