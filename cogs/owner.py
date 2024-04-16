import discord
from discord.ext import commands

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        print("Initialized owner cog")

    @commands.is_owner()
    @commands.command()
    async def syncslash(self, ctx):
        await self.bot.tree.sync()
        await ctx.send("Synced slash commands")

async def setup(bot):
    await bot.add_cog(Owner(bot))
