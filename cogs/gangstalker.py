import discord
from discord.ext import commands
from io import BytesIO
import sqlite3

# Init DB
conn = sqlite3.connect('bot.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS gangstalker (
        id INTEGER PRIMARY KEY,
        member INTEGER DEFAULT 0,
        guild INTEGAR DEFAULT 0,
        channel INTEGAR DEFAULT 0)
''')
conn.commit()

class Gangstalker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild == None:
            return
        channel_id = verify_gangstalk(message.author.id, message.guild.id)
        if channel_id == 0:
            return
        channel = self.bot.get_channel(channel_id)
        if message.content:
            await channel.send(f'{message.author.display_name}: {message.content}')
        if message.attachments:
            for attachment in message.attachments:
                file = await attachment.read()
                mirror = discord.File(BytesIO(file), filename=attachment.filename)
                await channel.send(f'{message.author.display_name}: {attachment.url}', file=mirror)

    @commands.command()
    @commands.is_owner()
    async def gangstalk(self, ctx, member: discord.Member = None, channel: discord.TextChannel = None):
        if ctx.guild == None:
            return
        if member == None:
            await ctx.send("Didn't select member")
            return
        if channel == None:
            await ctx.send("Didn't select channel")
            return
        if member.bot == True:
            await ctx.send("We can't gangstalk our own people")
            return
        channel_id = verify_gangstalk(member.id, ctx.guild.id)
        if channel_id != 0:
            await ctx.send("Gangstalking agents are already activated for this person")
            return
        create_gangstalk(member.id, ctx.guild.id, channel.id)
        await ctx.send("Gangstalking agents are now setup")

    @commands.command()
    @commands.is_owner()
    async def ungangstalk(self, ctx, member: discord.Member = None):
        if ctx.guild == None:
            return
        if member == None:
            await ctx.send("Didn't select member")
            return
        channel_id = verify_gangstalk(member.id, ctx.guild.id)
        if channel_id == 0:
            await ctx.send("Gangstalking agents aren't activated for this person")
            return
        remove_gangstalk(member.id, ctx.guild.id)
        await ctx.send("Gangstalking agents are now gone....")
        

def create_gangstalk(member_id, guild_id, channel_id):
    cursor.execute('INSERT INTO gangstalker (id, member, guild, channel) VALUES (NULL, ?, ?, ?)', (member_id, guild_id, channel_id))
    conn.commit()

def remove_gangstalk(member_id, guild_id):
    cursor.execute('DELETE FROM gangstalker WHERE member = ? AND guild = ?', (member_id, guild_id))
    conn.commit()

def verify_gangstalk(member_id, guild_id):
    cursor.execute('SELECT channel FROM gangstalker WHERE member = ? AND guild = ?', (member_id, guild_id))
    result = cursor.fetchone()
    return result[0] if result else 0

async def setup(bot):
    await bot.add_cog(Gangstalker(bot))

print("Initialized gangstalker cog")