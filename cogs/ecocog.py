import discord
from discord.ext import commands
import json
import datetime
import asyncio
import config


class item_manager:
    def __init__(self, user:discord.User, bot):
        self.user = user
        self.bot = bot
        self.items = self.items_add()


    def items_add(self):
        cur = self.bot.con.cursor()
        cur.execute("SELECT * FROM inventory WHERE user = ?", (self.user.id, ))
        q = cur.fetchone()
        if q == None:
            cur.execute("INSERT INTO inventory VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (self.user.id, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
            self.bot.con.commit()
            self.items = self.items_add()
        else:
            items = []
            with open("level.json", "r") as f:
                g = json.load(f)
                i = g["Items"]
                for n in range(len(i)):
                    if n == 0:
                        pass
                    else:
                        items.append((i[n]["name"], q[n], i[n]["price"]))
            return items
    
    async def remove(self, item:int):
        if self.items[item - 1][1] > 0:
            cur = self.bot.con.cursor()
            namt = self.items[item - 1][1] - 1
            cur.execute(f"UPDATE inventory SET i{item} = ? where USER = ?", (namt, self.user.id))
            self.bot.con.commit()
            return [True, f"{self.user.name} has used a {self.items[item - 1][0]}"]
        else:
            return [False, f"{self.user.name} didnt have any to use though"]

    async def add(self, item:int):
        cur = self.bot.con.cursor()
        namt = self.items[item - 1][1] + 1
        cur.execute("SELECT * FROM economy WHERE user = ?", (self.user.id, ))
        q = cur.fetchone()
        bal = q[1]
        nbal = bal - self.items[item - 1][2]
        if nbal > 0:
            cur.execute("UPDATE economy SET money = ? WHERE user = ?", (nbal, self.user.id))
            cur.execute(f"UPDATE inventory SET i{item} = ? where USER = ?", (namt, self.user.id))
            self.bot.con.commit()
            return f"{self.user.name} now has {nbal} and bought a {self.items[item - 1][0]}"
        else:
            return f"{self.user.name} doesnt have enough money to buy this item"

class item_usage:
    def __init__(self, user:discord.Member, assaulter:discord.Member, bot):
        self.bot = bot
        self.user = user
        self.assaulter = assaulter
        self.items = self.item_list()
        self.items_embed = self.item_grab()
        self.guild = config.debug_guild
        self.view = self.item_view(self.assaulter, self.user, self.guild, self.items)


    class item_view(discord.ui.View):
        def __init__(self, user: discord.Member, user2:discord.Member, guild, items:list, bot):
            super().__init__(timeout=90)
            self.bot = bot
            self.u1 = user
            self.u2 = user2
            self.guild = guild
            self.items = items
            

        @discord.ui.button(label="Use", style=discord.ButtonStyle.green)
        async def urc_use(self, button, interaction:discord.Interaction):
            guild = self.bot.get_guild(self.guild)
            user = guild.get_member(self.u1)
            victim = guild.get_member(interaction.user.id)
            h = item_manager(victim, self.bot)
            i = await h.remove(1)
            await interaction.response.send_message(i[1])
            if i[0] == False:
                pass
            else:
                role = guild.get_role(1047350121458839574)
                if role in user.roles:
                    await user.remove_roles(role)
                await user.timeout_for(duration=datetime.timedelta(minutes=5))
                await victim.remove_timeout()
                if isinstance(interaction.channel, discord.PartialMessageable):
                    channel = await guild.fetch_channel(1066012570143707167)
                    await channel.send("Uno Reverse used")
                await interaction.channel.send(f"{user.name} has been timed out for 5 minutes, and you have been removed from timeout")
                await interaction.message.edit(view=None)
                o = item_usage(user=user, assaulter=interaction.user.id, bot=self.bot)
                if o.items[0][1] != 0:
                    await user.send(embed=o.items_embed, view=o.view)



    def item_list(self):
        i = item_manager(self.user, self.bot)
        items = []
        for item in i.items:
            items.append(f"{item[0]}: {item[1]}")
        return items

    def item_grab(self):
        i = item_manager(self.user, self.bot)
        items = []
        for item in i.items:
            items.append(f"{item[0]}: {item[1]}")
        embed = discord.Embed(title=f"{self.user.name}'s inventory", color=accent_check(self.user), description="\n".join(items))
        return embed


class money_manager:
    def __init__(self, user1: discord.Member, user2: discord.Member, bot):
        self.user_1 = user1
        self.user_2 = user2
        self.bot = bot
        self.u1_bal = self.set_bal(1)
        self.u2_bal = self.set_bal(2)

    def set_bal(self, user:int):
        cur = self.bot.con.cursor()
        if user == 1:
            cur.execute("SELECT * FROM economy WHERE user = ?", (self.user_1.id, ))
            q = cur.fetchone()
            return q[1]
        else:
            cur.execute("SELECT * FROM economy WHERE user = ?", (self.user_2.id, ))
            q = cur.fetchone()
            return q[1]

    def pay(self, amt:int):
        u1_nbal = self.u1_bal - amt
        u2_nbal = self.u2_bal + amt
        if u1_nbal > 0:
            cur = self.bot.con.cursor()
            cur.execute("UPDATE economy SET money = ? WHERE user = ?", (u1_nbal, self.user_1.id))
            cur.execute("UPDATE economy SET money = ? WHERE user = ?", (u2_nbal, self.user_2.id))
            self.bot.con.commit()
            return f"{self.user_1.name} now has {u1_nbal}\n{self.user_2.name} now has {u2_nbal}"
        else:
            return f"Not enough Money in {self.user_1.name}'s profile"

class ShopView(discord.ui.View):
    def __init__(self, user:discord.Member, bot):
        super().__init__(timeout=60)
        self.bot = bot
        self.user = user
        self.bal = self.user_bal()
        self.guild = self.bot.get_guild(config.debug_guild)

    def user_bal(self):
        cur = self.bot.con.cursor()
        cur.execute("SELECT * FROM economy WHERE user = ?", (self.user.id, ))
        q = cur.fetchone()
        bal = q[1]
        return bal
    
    def check(self, m: discord.Message):  # m = discord.Message.
        return m.author.id == self.user.id and m.channel.id == self.message.channel.id 

    @discord.ui.button(label="Timeout User", style=discord.ButtonStyle.red)
    async def time_out(self, button, interaction:discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("You need to run this command to buy items", ephemeral=True)
        else:
            if self.bal < 500:
                await interaction.response.send_message("You do not have enough money to buy this", ephemeral=True)
            else:
                try:
                    await interaction.response.send_message("Please input a user id to timeout", ephemeral=True)
                    msg = await self.bot.wait_for(event="message", check=self.check, timeout=60)
                except asyncio.TimeoutError:
                    await interaction.response.send_message("You didnt reply fast enough")
                else:
                    try:
                        if isinstance(interaction.channel, discord.PartialMessageable):
                            pass
                        else:
                            await msg.delete()
                        user = await self.guild.fetch_member(msg.content)
                    except discord.errors.HTTPException:
                        await interaction.response.send_message("This is an invalid id")
                    else:
                        cur = self.bot.con.cursor()
                        role = self.guild.get_role(1047350121458839574)
                        if role in user.roles:
                            await user.remove_roles(role)
                        nbal = self.bal - 500
                        cur.execute("UPDATE economy SET money = ? WHERE user = ?", (nbal, self.user.id))
                        self.bot.con.commit()
                        await user.timeout_for(duration=datetime.timedelta(minutes=5))
                        if isinstance(interaction.channel, discord.PartialMessageable):
                            channel = await self.guild.fetch_channel(1066012570143707167)
                            await channel.send("Timeout used in dms")
                        await interaction.channel.send(f"{user.name} has been timed out for 5 minutes")
                        await interaction.message.edit(view=None)
                        o = item_usage(user=user, assaulter=interaction.user.id, bot=self.bot)
                        if o.items[0][1] != 0:
                            await user.send(embed=o.items_embed, view=o.view)

    @discord.ui.button(label="Uno Reverse Card", style=discord.ButtonStyle.blurple)
    async def urc_buy(self, button, interaction:discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("You need to run this command to buy items", ephemeral=True)
        else:
            item_m = item_manager(self.user, self.bot)
            result = await item_m.add(1)
            embed = discord.Embed(title=f"{interaction.user.name} has bought an item", color=accent_check(interaction.user), description=result)
            await interaction.response.send_message(embed=embed)
            await interaction.message.edit(view=None)


    async def on_timeout(self):
        if self.message.components == None:
            pass
        else:
            await self.message.edit(view=None)

def accent_check(user:discord.Member):
    if user.accent_color == None:
        return 0xb00b13
    else:
        return user.accent_color

class economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def pf(self, ctx, user:discord.Member = None):
        if user == None:
            user = ctx.author
        cur = self.bot.con.cursor()
        cur.execute("SELECT * FROM economy WHERE user = ?", (user.id, ))
        q = cur.fetchone()
        if q == None:
            await ctx.respond("This user apparently hasnt talked here yet, kinda rude ngl. Its alright tho, I fucked their mom", ephemeral=True)
        else:
            embed = discord.Embed(title=f"{user.name}'s Profile", color=discord.Color.lighter_gray(), description='\n'.join([
                f"**Money:**\n{q[1]}",
                f"**Reps:**\n{q[2]}",
                f"**Experience:**\n{q[3]}",
                f"**Level:**\n{q[4]}"
            ]))
            await ctx.respond(embed=embed)

    @commands.user_command()
    async def profile(self, ctx, user:discord.Member):
        cur = self.bot.con.cursor()
        cur.execute("SELECT * FROM economy WHERE user = ?", (user.id, ))
        q = cur.fetchone()
        if q == None:
            await ctx.respond("This user apparently hasnt talked here yet, kinda rude ngl. Its alright tho, I fucked their mom", ephemeral=True)
        else:
            embed = discord.Embed(title=f"{user.name}'s Profile", color=discord.Color.lighter_gray(), description='\n'.join([
                f"**Money:**\n{q[1]}",
                f"**Reps:**\n{q[2]}",
                f"**Experience:**\n{q[3]}",
                f"**Level:**\n{q[4]}"
            ]))
            await ctx.respond(embed=embed)

    @commands.slash_command()
    async def pay(self, ctx, user: discord.Member, amt:int):
        transaction = money_manager(ctx.author, user, self.bot).pay(amt)
        embed = discord.Embed(title=f"{ctx.author.name} has paid {user.name}", color=accent_check(ctx.author), description=transaction)
        await ctx.respond(embed=embed)

    @commands.slash_command()
    async def shop(self, ctx):
        embed = discord.Embed(title="Shop", description="**Timeout User**:\n**costs 500**\n Use this to time a user out for 5 minutes\n**Uno Reverse Card**:\n**costs 350**\nadds a uno reverse card to your inventory, which can be used to reverse a punishment", color=0xb00b13)
        await ctx.respond(embed=embed, view=ShopView(ctx.author, self.bot))

    @commands.slash_command(description= "A command to view your inventory")
    async def inventory(self, ctx):
        i = item_manager(ctx.author, self.bot)
        items = []
        for item in i.items:
            items.append(f"{item[0]}: {item[1]}")
        embed = discord.Embed(title=f"{ctx.author.name}'s inventory", color=accent_check(ctx.author), description="\n".join(items))
        await ctx.respond(embed=embed, ephemeral=True)
