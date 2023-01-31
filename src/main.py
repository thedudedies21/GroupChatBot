import discord
from discord.ext import commands
from sqlite3 import Connection

class testBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remove_command("Help")
        self.setup()


    def setup(self):
        self.con = Connection('daddy.db')
        cur = self.con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS roles(
                user INTEGER NOT NULL UNIQUE,
                role_id INTEGER NOT NULL UNIQUE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user(
                member INTEGER NOT NULL UNIQUE, 
                times_quoted INTEGER NOT NULL
            ) 
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quotes(
                message_id INTEGER NOT NULL, 
                content STRING NOT NULL, 
                author INTEGER NOT NULL,
                month INTEGER NOT NULL, 
                day INTEGER NOT NULL, 
                year INTEGER NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS economy(
                user INTEGER NOT NULL UNIQUE,
                money INTEGER NOT NULL,
                reps INTEGER NOT NULL, 
                experience INTEGER NOT NULL,
                level INTEGER NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory(
                user INTEGER NOT NULL UNIQUE,
                i1 INTEGER NOT NULL, 
                i2 INTEGER NOT NULL,
                i3 INTEGER NOT NULL, 
                i4 INTEGER NOT NULL, 
                i5 INTEGER NOT NULL, 
                i6 INTEGER NOT NULL, 
                i7 INTEGER NOT NULL, 
                i8 INTEGER NOT NULL, 
                i9 INTEGER NOT NULL, 
                i10 INTEGER NOT NULL
            )
        """)
        self.con.commit()

    async def on_ready(self):
        print(f"{self.user.name} has logged in")
        await self.change_presence(activity=discord.Game(name="with your mom"))

    def update_economy(self, user:discord.Member, ammount:int, option:int):
        if option == 1:
            cur = self.con.cursor()
            cur.execute("SELECT * FROM economy WEHRE user = ?", (user.id, ))
            q = cur.fetchone()
            oamt = q[1]
            namt = ammount + oamt
            cur.execute("UPDATE economy SET money = ? WHERE user = ?", (namt, user.id))
            self.con.commit()
        else:
            cur = self.con.cursor()
            cur.execute("SELECT * FROM economy WEHRE user = ?", (user.id, ))
            q = cur.fetchone()
            oamt = q[1]
            namt = oamt - ammount
            cur.execute("UPDATE economy SET money = ? WHERE user = ?", (namt, user.id))
            self.con.commit()

    def update_table(self, sqlite:str, tuple2:tuple):
        cur = self.con.cursor()
        cur.execute(f"{sqlite}", tuple2)
        self.con.commit()

    def naive_cursor(self, sqlite:str, tuple2:tuple):
        cur = self.con.cursor()
        cur.execute(f"{sqlite}", tuple2)
        q = cur.fetchone()
        cur.close()
        return q
        



    