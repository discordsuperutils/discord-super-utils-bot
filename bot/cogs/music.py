import time
from typing import Optional

import discord
import discordSuperUtils
from discord.ext import commands


class Music(commands.Cog, discordSuperUtils.CogManager.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client_secret = "876b40c7928e4d43bd07ae5f438794b6"
        self.client_id = "579dde2c1fe64feca4f3bd22e9a92ef9"
        self.MusicManager = discordSuperUtils.MusicManager(self.bot,
                                                           spotify_support=True,
                                                           client_secret=self.client_secret,
                                                           client_id=self.client_id)
        super().__init__()

    @staticmethod
    def __format_duration(duration: Optional[float]) -> str:
        return time.strftime("%H:%M:%S", time.gmtime(duration)) if duration != "LIVE" else duration

    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_music_error(self, ctx, error):
        embed = discord.Embed(
            title="Error!",
            color=0xff0000
        )

        if isinstance(error, discordSuperUtils.NotPlaying):
            embed.description = "I am not playing anything!"
            await ctx.send(embed=embed)

        elif isinstance(error, discordSuperUtils.NotConnected):
            embed.description = "I am not connected to a voice channel!"
            await ctx.send(embed=embed)

        elif isinstance(error, discordSuperUtils.NotPaused):
            embed.description = "The currently playing player is not paused!"
            await ctx.send(embed=embed)

        elif isinstance(error, discordSuperUtils.QueueEmpty):
            embed.description = "The queue is empty!"
            await ctx.send(embed=embed)

        elif isinstance(error, discordSuperUtils.AlreadyConnected):
            embed.description = "I am already connected to a voice channel!"
            await ctx.send(embed=embed)

        elif isinstance(error, discordSuperUtils.QueueError):
            embed.description = "There has been a queue error!"
            await ctx.send(embed=embed)

        elif isinstance(error, discordSuperUtils.SkipError):
            embed.description = "There has been an error while skipping!"
            await ctx.send(embed=embed)

        elif isinstance(error, discordSuperUtils.UserNotConnected):
            embed.description = "User is not connected to a voice channel!"
            await ctx.send(embed=embed)

        elif isinstance(error, discordSuperUtils.InvalidSkipIndex):
            embed.description = "That skip index is invalid!"
            await ctx.send(embed=embed)

        else:
            print('unexpected err')
            raise error

    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_play(self, ctx, player):
        embed = discord.Embed(
            title="Playing Song...",
            color=0x00ff00
        )

        embed.add_field(name="Title", value=f"[{player}]({player.url})")
        embed.add_field(name="Duration", value=self.__format_duration(player.duration), inline=False)

        await ctx.send(embed=embed)

    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_queue_end(self, ctx):
        print(f"The queue has ended in {ctx}")
        # You could wait and check activity, etc...

    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_inactivity_disconnect(self, ctx):
        print(f"I have left {ctx} due to inactivity..")

    @commands.command()
    async def leave(self, ctx):
        if await self.MusicManager.leave(ctx):
            await ctx.send(embed=discord.Embed(
                title="Left Voice Channel",
                description=f"I have left ...",
                color=0x00ff00
            ))

    @commands.command()
    async def np(self, ctx):
        if player := await self.MusicManager.now_playing(ctx):
            duration_played = await self.MusicManager.get_player_played_duration(ctx, player)

            embed = discord.Embed(
                title="Currently Playing",
                color=0x00ff00
            )

            embed.add_field(name="Title", value=f"[{player}]({player.url})")
            embed.add_field(name="Duration",
                            value=f'{self.__format_duration(duration_played)} /'
                                  f' {self.__format_duration(player.duration)}', inline=False)

            await ctx.send(embed=embed)

    @commands.command()
    async def join(self, ctx):
        if await self.MusicManager.join(ctx):
            await ctx.send(embed=discord.Embed(
                title="Joined Voice Channel",
                description=f"I have joined ...",
                color=0x00ff00
            ))

    @commands.command()
    async def play(self, ctx, *, query: str):
        async with ctx.typing():
            player = await self.MusicManager.create_player(query)

        if player:
            if await self.MusicManager.queue_add(players=player, ctx=ctx) and not await self.MusicManager.play(ctx):
                await ctx.send("Added to queue")
        else:
            await ctx.send("Query not found.")

    @commands.command()
    async def pause(self, ctx):
        if await self.MusicManager.pause(ctx):
            await ctx.send("Player paused.")

    @commands.command()
    async def resume(self, ctx):
        if await self.MusicManager.resume(ctx):
            await ctx.send("Player resumed.")

    @commands.command()
    async def volume(self, ctx, volume: int = None):
        current_volume = await self.MusicManager.volume(ctx, volume)

        await ctx.send(
            embed=discord.Embed(
                title="Current Volume",
                description=f"The current volume is {current_volume}%",
                color=0x00ff00
            ) if volume is None else discord.Embed(
                title="Volume Changed",
                description=f"Volume has been changed to {current_volume}%",
                color=0x00ff00
            ))

    @commands.command()
    async def loop(self, ctx):
        loop_state = await self.MusicManager.loop(ctx)
        await ctx.send(embed=discord.Embed(
            title="Loop Toggled",
            description=f"Loop is now {'enabled' if loop_state else 'disabled'}.",
            color=0x00ff00
        ))

    @commands.command()
    async def queueloop(self, ctx):
        loop_state = await self.MusicManager.queueloop(ctx)
        await ctx.send(embed=discord.Embed(
            title="Queue Loop Toggled",
            description=f"Queue loop is now {'enabled' if loop_state else 'disabled'}.",
            color=0x00ff00
        ))

    @commands.command()
    async def history(self, ctx):
        embeds = discordSuperUtils.generate_embeds(await self.MusicManager.history(ctx),
                                                   "Song History",
                                                   "Shows all played songs",
                                                   25,
                                                   string_format="Title: '{}'")

        page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
        await page_manager.run()

    @commands.command()
    async def skip(self, ctx, index: int = None):
        skipped_player = await self.MusicManager.skip(ctx, index)
        await ctx.send(embed=discord.Embed(
            title=f"Skipped to {index}" if index is not None else "Skipped to Next Song",
            description=f"Skipped to '{skipped_player}'.",
            color=0x00ff00
        ))

    @commands.command()
    async def queue(self, ctx):
        embeds = discordSuperUtils.generate_embeds(await self.MusicManager.get_queue(ctx),
                                                   "Queue",
                                                   f"Now Playing: {await self.MusicManager.now_playing(ctx)}",
                                                   25,
                                                   string_format="Title: '{}'")
        page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
        await page_manager.run()


def setup(bot):
    bot.add_cog(Music(bot))
