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
        self.MusicManager = discordSuperUtils.MusicManager(
            self.bot,
            spotify_support=True,
            client_secret=self.client_secret,
            client_id=self.client_id,
        )
        super().__init__()

    @staticmethod
    def __format_duration(duration: Optional[float]) -> str:
        return (
            time.strftime("%H:%M:%S", time.gmtime(duration))
            if duration != "LIVE"
            else duration
        )

    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_music_error(self, ctx, error):
        errors = {
            discordSuperUtils.NotPlaying: "I am not playing anything!",
            discordSuperUtils.NotConnected: "I am not connected to a voice channel!",
            discordSuperUtils.NotPaused: "The currently playing player is not paused!",
            discordSuperUtils.QueueEmpty: "The queue is empty!",
            discordSuperUtils.AlreadyConnected: "I am already connected to a voice channel!",
            discordSuperUtils.QueueError: "There has been a queue error!",
            discordSuperUtils.SkipError: "There is no song to skip to!",
            discordSuperUtils.UserNotConnected: "User is not connected to a voice channel!",
            discordSuperUtils.InvalidSkipIndex: "That skip index is invalid!",
        }

        embed = discord.Embed(title="Error!", color=0xFF0000)

        for error_type, response in errors.items():
            if isinstance(error, error_type):
                embed.description = response
                await ctx.send(embed=embed)
                return

        print("unexpected err")
        raise error

    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_play(self, ctx, player):
        embed = discord.Embed(title="Playing Song...", color=0x00FF00)

        embed.add_field(name="Title", value=f"[{player}]({player.url})")
        embed.add_field(
            name="Duration", value=self.__format_duration(player.duration), inline=False
        )
        embed.add_field(
            name="Requester",
            value=player.requester and player.requester.mention,
            inline=False,
        )

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
        if channel := await self.MusicManager.leave(ctx):
            await ctx.send(
                embed=discord.Embed(
                    title="Left Voice Channel",
                    description=f"I have left {channel.mention}",
                    color=0x00FF00,
                )
            )

    @commands.command(aliases=["nowplaying"])
    async def np(self, ctx):
        if player := await self.MusicManager.now_playing(ctx):
            duration_played = await self.MusicManager.get_player_played_duration(
                ctx, player
            )

            embed = discord.Embed(title="Currently Playing", color=0x00FF00)

            embed.add_field(name="Title", value=f"[{player}]({player.url})")
            embed.add_field(
                name="Duration",
                value=f"{self.__format_duration(duration_played)} /"
                f" {self.__format_duration(player.duration)}",
                inline=False,
            )
            embed.add_field(
                name="Requester",
                value=player.requester and player.requester.mention,
                inline=False,
            )

            await ctx.send(embed=embed)

    @commands.command()
    async def join(self, ctx):
        if channel := await self.MusicManager.join(ctx):
            await ctx.send(
                embed=discord.Embed(
                    title="Joined Voice Channel",
                    description=f"I have joined {channel.mention}",
                    color=0x00FF00,
                )
            )

    @commands.command(aliases=["p"])
    async def play(self, ctx, *, query: str):
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.MusicManager.join(ctx)

        async with ctx.typing():
            player = await self.MusicManager.create_player(query, ctx.author)

        if player:
            if await self.MusicManager.queue_add(
                players=player, ctx=ctx
            ) and not await self.MusicManager.play(ctx):
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
        if current_volume := await self.MusicManager.volume(ctx, volume):
            await ctx.send(
                embed=discord.Embed(
                    title="Current Volume",
                    description=f"The current volume is {current_volume}%",
                    color=0x00FF00,
                )
                if volume is None
                else discord.Embed(
                    title="Volume Changed",
                    description=f"Volume has been changed to {current_volume}%",
                    color=0x00FF00,
                )
            )

    @commands.command()
    async def loop(self, ctx):
        loop_state = await self.MusicManager.loop(ctx)

        if loop_state is not None:
            await ctx.send(
                embed=discord.Embed(
                    title="Loop Toggled",
                    description=f"Loop is now {'enabled' if loop_state else 'disabled'}.",
                    color=0x00FF00,
                )
            )

    @commands.command()
    async def queueloop(self, ctx):
        loop_state = await self.MusicManager.queueloop(ctx)

        if loop_state is not None:
            await ctx.send(
                embed=discord.Embed(
                    title="Queue Loop Toggled",
                    description=f"Queue loop is now {'enabled' if loop_state else 'disabled'}.",
                    color=0x00FF00,
                )
            )

    @commands.command()
    async def history(self, ctx):
        if queue := await self.MusicManager.get_queue(ctx):
            formatted_history = [
                f"Title: '{x.title}'\nRequester: {x.requester and x.requester.mention}"
                for x in queue.history
            ]

            embeds = discordSuperUtils.generate_embeds(
                formatted_history,
                "Song History",
                "Shows all played songs",
                25,
                string_format="Title: '{}'",
            )

            page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
            await page_manager.run()

    @commands.command()
    async def skip(self, ctx, index: int = None):
        if skipped_player := await self.MusicManager.skip(ctx, index):
            await ctx.send(
                embed=discord.Embed(
                    title=f"Skipped to {index}"
                    if index is not None
                    else "Skipped to Next Song",
                    description=f"Skipped to '{skipped_player}'.",
                    color=0x00FF00,
                )
            )

    @commands.command()
    async def lyrics(self, ctx, query: str = None):
        if response := await self.MusicManager.lyrics(ctx, query):
            title, author, query_lyrics = response

            splitted = query_lyrics.split("\n")
            res = []
            current = ""
            for i, split in enumerate(splitted):
                if len(splitted) <= i + 1 or len(current) + len(splitted[i + 1]) > 1024:
                    res.append(current)
                    current = ""
                    continue
                current += split + "\n"

            page_manager = discordSuperUtils.PageManager(
                ctx,
                [
                    discord.Embed(
                        title=f"Lyrics for '{title}' by '{author}', (Page {i + 1}/{len(res)})",
                        description=x,
                    )
                    for i, x in enumerate(res)
                ],
                public=True,
            )
            await page_manager.run()
        else:
            await ctx.send("No lyrics found.")

    @commands.command()
    async def shuffle(self, ctx):
        shuffle_state = await self.MusicManager.shuffle(ctx)

        if shuffle_state is not None:
            await ctx.send(
                embed=discord.Embed(
                    title="Shuffle Toggled",
                    description=f"Shuffle is now {'enabled' if shuffle_state else 'disabled'}.",
                    color=0x00FF00,
                )
            )

    @commands.command()
    async def autoplay(self, ctx):
        autoplay_state = await self.MusicManager.autoplay(ctx)

        if autoplay_state is not None:
            await ctx.send(
                embed=discord.Embed(
                    title="Autoplay Toggled",
                    description=f"Autoplay is now {'enabled' if autoplay_state else 'disabled'}.",
                    color=0x00FF00,
                )
            )

    @commands.command()
    async def queue(self, ctx):
        if queue := await self.MusicManager.get_queue(ctx):
            formatted_queue = [
                f"Title: '{x.title}\nRequester: {x.requester and x.requester.mention}"
                for x in queue.queue
            ]

            embeds = discordSuperUtils.generate_embeds(
                formatted_queue,
                "Queue",
                f"Now Playing: {await self.MusicManager.now_playing(ctx)}",
                25,
                string_format="Title: '{}'",
            )
            page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
            await page_manager.run()

    @commands.command()
    async def ls(self, ctx):
        if queue := await self.MusicManager.get_queue(ctx):
            loop = queue.loop
            loop_status = None

            if loop == discordSuperUtils.Loops.LOOP:
                loop_status = "Looping enabled."

            elif loop == discordSuperUtils.Loops.QUEUE_LOOP:
                loop_status = "Queue looping enabled."

            elif loop == discordSuperUtils.Loops.NO_LOOP:
                loop_status = "No loop enabled."

            if loop_status:
                embed = discord.Embed(title=loop_status, color=0x00FF00)

                await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Music(bot))
