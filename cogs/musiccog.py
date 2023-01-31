from discord.ext import tasks, commands
import wavelink
from wavelink.ext import spotify
from wavelink import errors as we
import discord


class Music(commands.Cog):
    """Music cog to hold Wavelink related commands and listeners."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.loop.create_task(self.connect_nodes())
        self.vc:wavelink.Player = None

    async def connect_nodes(self):
        """Connect to our Lavalink nodes."""
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(
            bot=self.bot,
            host='host',
            port=int,
            password='password',
        )

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Event fired when a node has finished connecting."""
        print(f'Node: <{node.identifier}> is ready!')

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        if not self.vc.queue.is_empty:
            x = await self.vc.queue.get_wait()
            await self.vc.play(x)
        else:
            await self.vc.disconnect()


    @commands.command()
    async def play(self, ctx: commands.Context, *, search: wavelink.YouTubeTrack):
        """Play a song with the given search query.
        If not connected, connect to our voice channel.
        """
        if not ctx.voice_client:
            self.vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        if self.vc.is_playing():
            await self.vc.queue.put_wait(search)
            await ctx.send("Added to queue")
        else:
            await self.vc.play(search)
            await ctx.send("Playing")


    @commands.command()
    async def pause(self, ctx: commands.Context):
        if self.vc == None:
            await ctx.send("There is no player active")
        else:
            if self.vc.is_paused():
                await self.vc.resume()
                await ctx.send("Music Resumed")
            else:
                await self.vc.pause()
                await ctx.send("Music paused")

    @commands.command()
    async def skip(self, ctx):
        if not self.vc.queue.is_empty:
            await self.vc.stop()
        else:
            await self.vc.disconnect()
            await ctx.send("Session Ended")


    @commands.command()
    async def queue(self, ctx):
        tracks = []
        for song in self.vc.queue:
            y = (song.info["title"], song.info["author"])
            tracks.append(y)
        if len(tracks) == 0:
            await ctx.send("Queue is empty")
        else:
            embed = discord.Embed(title="Song Queue", color=0x00ffff)
            for i in tracks:
                embed.add_field(name="Song", value=f"{i[0]}\n{i[1]}", inline=False)
            await ctx.send(embed=embed)
