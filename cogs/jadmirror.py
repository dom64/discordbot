import discord
from discord.ext import commands
from io import BytesIO

class JadMirror(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == 176322126129790976:
            channel = self.bot.get_channel(1093261714931322901)
            if message.content:
                await channel.send(f'{message.author.display_name}: {message.content}')
            if message.attachments:
                for attachment in message.attachments:
                    file = await attachment.read()
                    mirror = discord.File(BytesIO(file), filename=attachment.filename)
                    await channel.send(f'{message.author.display_name}: {attachment.url}', file=mirror)

async def setup(bot):
    await bot.add_cog(JadMirror(bot))

print("Initialized jad mirror cog")