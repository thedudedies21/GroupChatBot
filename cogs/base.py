import discord
from discord.ext import commands
import random
from src import testBot
import datetime
import config

class colorstuff():
    def __init__(self, hex):
        self.hex = hex
        self.rgb = []
        for i in (0, 2, 4):
            decimal = int(self.hex[i:i+2], 16)
            self.rgb.append(decimal)

    async def getIfromRGB(self):
        red = self.rgb[0]
        green = self.rgb[1]
        blue = self.rgb[2]
        rgbint = (red<<16) + (green<<8) + blue
        return rgbint

async def select():
    people = [] #insert characters or names here for the random attribute, used for games on Dead By Daylight where lobbies can be done custom
    selection = random.choice(people)
    return selection

class myView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)
        
    @discord.ui.button(label="New Killer", custom_id="killer", style=discord.ButtonStyle.red)
    async def killer_callback(self, button, interaction):
        selector = await select()
        embed = discord.Embed(title="The killer has been selected", colour=0x000003)
        embed.add_field(name="The killer will be:", value=f"{selector}")
        await interaction.response.send_message(embed=embed, view=myView())

    async def on_timeout(self):
        await self.message.edit(view=None)

def accent_check(user:discord.Member):
    if user.accent_color == None:
        return 0xb00b13
    else:
        return user.accent_color

class search:
    def __init__(self, day:int, month:int, text:str, bot, author:int = None):
        self.day = day
        self.bot = bot
        self.month = month
        self.text = text
        self.author = author

    async def date_search(self):
        resulution = []
        cur = self.bot.con.cursor()
        cur.execute("SELECT * FROM quotes WHERE month = ? AND day = ?", (self.month, self.day))
        q = cur.fetchall()
        for x in q:
            resulution.append(x)
        return resulution
                
    async def keyword_search(self):
        if self.text == ".":
            return "no_reults"
        resulution = []
        keyword = self.text
        cur = self.bot.con.cursor()
        cur.execute(f"SELECT * FROM quotes WHERE content LIKE '%{keyword}%'")
        q = cur.fetchall()
        for x in q:
            resulution.append(x)
        return resulution

    async def user_search(self):
        resulution = []
        user = self.author
        cur = self.bot.con.curspor()
        cur.execute("SELECT * FROM quotes WHERE author = ?", (self.author, ))
        q = cur.fetchall()
        for x in q:
            resulution.append(x)
        return resulution

class base_Cog(commands.Cog):
    def __init__(self, bot:testBot):
        self.bot = bot

    @commands.slash_command()
    async def select_killer(self, ctx):
        selected = await select()
        embed = discord.Embed(title="The killer has been selected", colour=0x000003)
        embed.add_field(name="The killer will be:", value=f"{selected}")
        await ctx.respond(embed=embed, view=myView())

    @commands.slash_command()
    async def setup(self, ctx, user: discord.Member):
        if ctx.author.id != 366098121941319680:
            await ctx.respond("This command can only be used by munchy for safety reasons", ephemeral=True)
        else:
            roleserver = self.bot.get_guild(config.debug_guild)
            role = roleserver.get_role(1047350121458839574)
            await user.add_roles(role)
            await ctx.respond(f"{user.name} has had the admin role added")

    @commands.slash_command(description="A command to give yourself a custom role")
    @discord.option(
        name="role_name",
        type=str, 
        description="The name of the role you want"
    )
    @discord.option(
        name="hex",
        type=str,
        description="The color hex you want to use, do not add #",
        required=False, 
        default='b00b1e'
    )
    async def color_role(self, ctx:discord.ApplicationContext, role_name:str, hex:str):
        userid = ctx.author.id
        cur = self.bot.con.cursor()
        cur.execute("SELECT * FROM roles WHERE user = ?", (userid, ))
        q = cur.fetchone()
        nhex = hex.upper()
        rgbcreator = colorstuff(hex=nhex)
        newint = await rgbcreator.getIfromRGB()
        if q == None:
            role = await ctx.guild.create_role(name=role_name, colour=newint)
            cur.execute("INSERT INTO roles VALUES(?, ?)", (userid, role.id))
            self.bot.con.commit()
            await ctx.respond(content=f"<@&{role.id}> has been created", allowed_mentions=discord.AllowedMentions(roles=True))
            await ctx.author.add_roles(role)
        else:
            role = ctx.guild.get_role(q[1])
            await role.edit(name=role_name, color=newint)
            await ctx.respond(content=f"<@&{role.id}> has been updated", allowed_mentions=discord.AllowedMentions(roles=True))
            if role not in ctx.author.roles:
                await ctx.author.add_roles(role)

    @commands.slash_command()
    async def quote(self, ctx, quote:str, author:discord.Member):
        cur = self.bot.con.cursor()
        embed = discord.Embed(title=f"{ctx.author.name} Quoted {author.name}", color=discord.colour.Color.red(), description=f"**'{quote}'**")
        embed.set_footer(text=f"-'{author.name}'")
        embed.set_thumbnail(url=f"{author.avatar.url}")
        await ctx.respond("Quote has been created, check <#1047340956954935346>")
        os = self.bot.get_guild(config.debug_guild)
        channel = os.get_channel(1047340956954935346)
        mess = await channel.send(embed=embed)
        aid = author.id
        date = [datetime.date.today().month, datetime.date.today().day, datetime.date.today().year]
        cur.execute("INSERT INTO quotes VALUES(?, ?, ?, ?, ?, ?)", (mess.id, quote, aid, date[0], date[1], date[2]))
        self.bot.con.commit()
        print(f"""{quote} was created on {'/'.join([
            str(date[0]), 
            str(date[1]), 
            str(date[2])]
            )}""")

    @commands.slash_command(description="Search quotes by date")
    @discord.option(
        name="type",
        description="Choose the type of search you want to do",
        choices=["date", "keyword", "user"], 
        required=False, 
        default="user"
    )
    @discord.option(
        name="month",
        description="Select the numeric value of the month",
        min_value=1, 
        max_value=12, 
        required=False,
    )
    @discord.option(
        name="day",
        description="Select the numeric value of the day of the month",
        min_value=1,
        max_value=31,
        required=False,
    )
    @discord.option(
        name="keyword",
        type=str,
        required=False
    )
    async def quote_search(self, ctx, type:str, month:int, day:int, keyword:str, user:discord.Member = None):
            if user == None:
                user = ctx.author
            if keyword == None:
                keyword = "."
            if day == None:
                day = datetime.date.today().day
            if month == None:
                month = datetime.date.today().month
            usernum = user.id
            stuff = search(day=day, month=month, text=keyword, author=usernum, bot=self.bot)
            colorlist = [0x710193, 0x00ff00, 0x000003, 0xfe019a]
            color = random.choice(colorlist)
            embed = discord.Embed(title="Returning Results!", color=color)
            if type == "user":
                result = await stuff.user_search()
                if len(result) == 0:
                    embed.add_field(name="No Quotes Found", value="Please try a different result")
                else:
                    for x in result:
                        embed.add_field(name="result", value="\n".join([
                            f"quote: {x[1]}", 
                            f"author: {user.name}"
                        ]), inline=False)
            elif type == "keyword":
                result = await stuff.keyword_search()
                if len(result) == 0:
                    embed.add_field(name="No Quotes Found", value="Please try a different result")
                else:
                    for x in result:
                        embed.add_field(name="result", value="\n".join([
                            f"quote: {x[1]}", 
                            f"author: {user.name}"
                        ]), inline=False)
            else:
                result = await stuff.date_search()
                if len(result) == 0:
                    embed.add_field(name="No Quotes Found", value="Please try a different result")
                else:
                    for x in result:
                        embed.add_field(name="result", value="\n".join([
                            f"quote: {x[1]}", 
                            f"author: {user.name}"
                        ]), inline=False)
            await ctx.respond(embed=embed)

    
    @commands.slash_command(description="Tips I felt that were important")
    async def tips(self, ctx):
        embed = discord.Embed(title="Tips!", color=accent_check(ctx.author), description="\n".join(
            [
                "You can use the bot to grind money in its dms, but the lootboxes will not spawn in dms", 
                "You can use the shop and timeout button in dms to target people in the server, even if you are already muted", 
                "Lootboxes spawn by choosing a number 0-16, and if it equals 13, a lootbox spawns. the odds are a little high, but you can do it, I believe in you!"
            ]
        ))
        await ctx.respond(embed=embed)