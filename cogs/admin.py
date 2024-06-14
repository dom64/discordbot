import discord
from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        print("Initialized admin cog")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def idban(self, ctx, user_id: int):
        user = await self.bot.fetch_user(user_id)
        await ctx.guild.ban(user)
        await ctx.send(f"User {user.name} has been banned")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.MemberNotFound):
            await ctx.send("Error: Member not found")
        else:
            raise error

async def setup(bot):
    await bot.add_cog(Admin(bot))
