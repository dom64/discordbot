import discord
from discord.ext import commands

class JadMirror(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == 176322126129790976:
            channel = self.bot.get_channel(1093261714931322901)
            await channel.send(f'{message.author.display_name}: {message.content}')

async def setup(bot):
    await bot.add_cog(JadMirror(bot))

print("Initialized jad mirror cog")