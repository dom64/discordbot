import discord
from discord.ext import commands

class OWO(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hug(self, ctx, target: discord.Member):
        await ctx.send(f'Hugs ')

async def setup(bot):
    await bot.add_cog(OWO(bot))

print("Initialized OWO cog")