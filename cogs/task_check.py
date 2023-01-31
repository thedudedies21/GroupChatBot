import discord
from discord.ext import commands, tasks
import random
import json
import datetime
import config

worked = []

def accent_check(user:discord.Member):
    if user.accent_color == None:
        return 0xb00b13
    else:
        return user.accent_color

class working:
    def __init__(self, bot):
        self.number = random.randint(1, 7)
        self.bot = bot
        self.min = self.set_min()
        self.max = self.set_max()
        print(f"{self.min} {self.max}")

    def set_max(self):
        if self.number == 1:
            return 200
        elif self.number == 2:
            return 210
        elif self.number == 3:
            return 190
        elif self.number == 4:
            return 175
        elif self.number == 5:
            return 225
        elif self.number == 6:
            return 240
        else:
            return 165

    def set_min(self):
        min = random.choice([120, 130, 110, 100])
        return min
        
    def get_reward(self):
        gift = random.randint(self.min, self.max)
        return gift

    async def update_user(self, duser:int, dchannel:int):
        cur = self.bot.con.cursor()
        cur.execute("SELECT * FROM economy WHERE user = ?", (duser, ))
        q = cur.fetchone()
        oamt = q[1]
        rew = self.get_reward()
        namt = oamt + rew
        oexp = q[3]
        nexp = oexp + 25
        olvl = q[4]
        guild = self.bot.get_guild(config.debug_guild)
        user = await self.bot.fetch_user(duser)
        with open("level.json", "r+") as f:
            l = json.load(f)
            g = l["Level_System"]
            i = g[olvl]
            reward = i["money"]
            if i["exp"] < nexp:
                clevel = olvl + 1
                channel = await guild.fetch_channel(dchannel)
                embed = discord.Embed(title=f"{user.name} has leveled up", color=accent_check(user), description=f"They have been rewarded {reward} dollars")
                await channel.send(embed=embed)
                famt = namt + reward
            else:
                clevel = olvl
                famt = namt
        cur.execute("UPDATE economy SET money = ?, experience = ?, level = ? WHERE user = ?", (famt, nexp, clevel, user.id))
        self.bot.con.commit()
        return rew

class lootBox:
    def __init__(self, message:discord.Message, bot):
        self.ammount = self.set_ammt()
        self.exp = self.set_exp()
        self.bot = bot
        self.message = message
        self.lbv = self.lootbox_view(reward=self.ammount, exp=self.exp, bot=self.bot)

    class lootbox_view(discord.ui.View):
        def __init__(self, reward:int, exp:int, bot):
            super().__init__(timeout=150)
            self.reward = reward
            self.exp = exp
            self.bot = bot
            self.claimed = False

        @discord.ui.button(label="Claim", style=discord.ButtonStyle.green)
        async def collect(self, button, interaction:discord.Interaction):
            if self.claimed != False:
                await interaction.response.send_message("This has already been claimed", ephemeral=True)
            else:
                self.claimed = True
                cur = self.bot.con.cursor()
                cur.execute("SELECT * FROM economy WHERE user = ?", (interaction.user.id, ))
                q = cur.fetchone()
                oamt = q[1]
                namt = oamt + self.reward
                oexp = q[3]
                nexp = oexp + self.exp
                olvl = q[4]
                with open("level.json", "r+") as f:
                    l = json.load(f)
                    g = l["Level_System"]
                    i = g[olvl]
                    reward = i["money"]
                    if i["exp"] < nexp:
                        clevel = olvl + 1
                        user = await self.bot.fetch_user(interaction.user.id)
                        embed = discord.Embed(title=f"{interaction.user.name} has leveled up", color=accent_check(user), description=f"They have been rewarded {reward} dollars")
                        await interaction.response.send_message(embed=embed)
                        famt = namt + reward
                    else:
                        await interaction.response.defer()
                        clevel = olvl
                        famt = namt
                rembed = discord.Embed(title="Lootbox Collected", color=0x028a0f, description=f"{interaction.user.name} has collected ${self.reward} and {self.exp} experience")
                await interaction.channel.send(embed=rembed)
                await interaction.message.edit(view=None)
                cur.execute("UPDATE economy SET money = ?, experience = ?, level = ? WHERE user = ?", (famt, nexp, clevel, interaction.user.id))
                self.bot.con.commit()

    def set_ammt(self):
        amt = random.randint(10, 20)
        return amt

    def set_exp(self):
        exp = random.randint(1, 3)
        return exp

    async def ini_lb(self):
        embed = discord.Embed(title="A lootbox has Appeared", color=0xe6cc00, description="Who will be the first to claim it?")
        if isinstance(self.message.channel, discord.channel.DMChannel):
            pass
        else:
            await self.message.channel.send(embed=embed, view=self.lbv)

        

    
current_shift = None

class TaskCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_shift = None
        self.worked = []
        self.new_work_cycle.start()
    
    @tasks.loop(hours=8)
    async def new_work_cycle(self):
        guild = self.bot.get_guild(config.debug_guild)
        channel = await guild.fetch_channel(1066012570143707167)
        self.worked.clear()
        x = working(bot=self.bot)
        self.current_shift = x
        embed = discord.Embed(title="Notice:", color=0x85bb65, description=f"The work command has been set\n**The new max is {x.max}**\n**The Current Min is {x.min}**")
        await channel.send(embed=embed)

    @new_work_cycle.before_loop
    async def wait_til_ready_cycle(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=30)
    async def return_admin(self):
        admin_ids = [415349166726971394, 366098121941319680, 339075120838606858, 700129522980356177, 886437640889593856, 558800844343214090, 680605479327498280]
        guild = self.bot.get_guild(config.debug_guild)
        role = guild.get_role(1047350121458839574)
        for id in admin_ids:
            member = await guild.fetch_member(id)
            if role not in member.roles:
                await member.add_roles(role)
            else:
                pass

    @return_admin.before_loop
    async def wait_for_ready(self):
        await self.bot.wait_until_ready()

    @commands.slash_command(description="Work once every 8 hours")
    async def work(self, ctx):
        if ctx.author.id not in worked:
            result = await self.current_shift.update_user(ctx.author.id, dchannel=ctx.channel.id)
            embed = discord.Embed(title=f"{ctx.author.name} has just finished their shift", color=accent_check(ctx.author), description=f"For their total take, they made {result} and gained 25 experience")
            self.worked.append(ctx.author.id)
            await ctx.respond(embed=embed)
        else:
            await ctx.respond("You have already worked during this work period", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        if message.author.id == self.bot.user.id:
            pass
        else:
            cur = self.bot.con.cursor()
            cur.execute("SELECT * FROM economy WHERE user = ?", (message.author.id, ))
            q = cur.fetchone()
            hb = random.randint(0, 16)
            randamt = random.randint(1, 3)
            if q == None:
                cur.execute("INSERT INTO economy VALUES(?, ?, ?, ?, ?)", (message.author.id, randamt, 0, 1, 1))
                self.bot.con.commit()
            else:
                oamt = q[1]
                namt = oamt + randamt
                oexp = q[3]
                nexp = oexp + 1
                olvl = q[4]
                with open("level.json", "r+") as f:
                    l = json.load(f)
                    g = l["Level_System"]
                    i = g[olvl]
                    reward = i["money"]
                    if i["exp"] < nexp:
                        clevel = olvl + 1
                        user = await self.bot.fetch_user(message.author.id)
                        embed = discord.Embed(title=f"{message.author.name} has leveled up", color=accent_check(user), description=f"They have been rewarded {reward} dollars")
                        await message.channel.send(embed=embed)
                        famt = namt + reward
                    else:
                        clevel = olvl
                        famt = namt
                cur.execute("UPDATE economy SET money = ?, experience = ?, level = ? WHERE user = ?", (famt, nexp, clevel, message.author.id))
                self.bot.con.commit()
                if hb == 13:
                    m = lootBox(message=message, bot=self.bot)
                    await m.ini_lb()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(title="New Member", color=0xf9c605)
        embed.add_field(name="Member Name:", value=f"{member.name}", inline=False)
        embed.set_footer(text="/".join([
            f"{datetime.date.today().month}",
            f"{datetime.date.today().day}",
            f"{datetime.date.today().year}"
        ]))
        mid = member.id
        guild = self.bot.get_guild(config.debug_guild)
        members = await guild.fetch_member(mid)
        role = guild.get_role(1052273758687211592)
        channel = guild.get_channel(1052266690857160744)
        await members.add_roles(role)
        await channel.send(embed=embed)