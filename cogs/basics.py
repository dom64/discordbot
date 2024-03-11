import discord
from discord.ext import commands

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Running as {self.bot.user}')

    @commands.Cog.listener()
    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')

    @commands.Cog.listener()
    async def on_message_delete(message):
        print(f'Message deleted in #{message.channel}: {message.content}')
    
    @commands.hybrid_command(name="ping", description="Pings the bot!")
    async def ping(self, ctx):
        await ctx.send(f"Pong!")

async def setup(bot):
    await bot.add_cog(Basic(bot))

print("Initialized basic cog")