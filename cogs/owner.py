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

    @commands.is_owner()
    @commands.command()
    async def sendmsg(self, ctx, user: discord.User, *, msg):
        await user.send(msg)
        await ctx.send("Message sent!")
    
    @sendmsg.error
    async def sendmsg_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.UserNotFound):
            await ctx.send("Error: Member not found")
        else:
            raise error

async def setup(bot):
    await bot.add_cog(Owner(bot))
