from src import testBot
import discord
import config
import ast
from discord.ext import commands
from cogs import Music, GbCog, economy, base_Cog, TaskCog

def insert_returns(body):
    # insert return stmt if the last expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the orelse
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # for with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body) 

intents = discord.Intents.all()

bot = testBot(command_prefix=commands.when_mentioned_or("?"), debug_guild=config.debug_guild, intents=intents)
bot.add_cog(Music(bot))
bot.add_cog(economy(bot))
bot.add_cog(GbCog(bot))
bot.add_cog(base_Cog(bot))
bot.add_cog(TaskCog(bot))

@bot.command()
async def eval_fn(ctx, *, cmd):
    if ctx.author.id == 366098121941319680:
        fn_name = "_eval_expr"

        cmd = cmd.strip("` ")

        # add a layer of indentation
        cmd = "\n".join(f"    {i}" for i in cmd.splitlines())

        # wrap in async def body
        body = f"async def {fn_name}():\n{cmd}"

        parsed = ast.parse(body)
        body = parsed.body[0].body

        insert_returns(body)

        env = {
            'py': None,
            'bot': bot,
            'discord': discord,
            'ctx': ctx,
            'con': bot.con,
            'cur': bot.con.cursor(),
            '__import__': __import__
        }
        exec(compile(parsed, filename="<ast>", mode="exec"), env)

        result = (await eval(f"{fn_name}()", env))

bot.run(config.token)