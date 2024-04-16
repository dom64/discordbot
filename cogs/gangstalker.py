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

    async def cog_load(self):
        print("Initialized gangstalker cog")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
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
    @commands.guild_only()
    async def gangstalk(self, ctx, member: discord.Member = None, channel: discord.TextChannel = None):
        if ctx.guild is None:
            return
        if member is None:
            await ctx.send("Didn't select member")
            return
        if channel is None:
            await ctx.send("Didn't select channel")
            return
        if member.bot is True:
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
    @commands.guild_only()
    async def ungangstalk(self, ctx, member: discord.Member = None):
        if ctx.guild is None:
            return
        if member is None:
            await ctx.send("Didn't select member")
            return
        channel_id = verify_gangstalk(member.id, ctx.guild.id)
        if channel_id == 0:
            await ctx.send("Gangstalking agents aren't activated for this person")
            return
        remove_gangstalk(member.id, ctx.guild.id)
        await ctx.send("Gangstalking agents are now gone....")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.MemberNotFound):
            await ctx.send("Error: Member not found")
        elif isinstance(error, discord.ext.commands.errors.ChannelNotFound):
            await ctx.send("Error: Channel not found")
        elif isinstance(error, discord.ext.commands.errors.NoPrivateMessage):
            print(f"{ctx.author} tried to use command in DMs")
        else:
            raise error

        
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