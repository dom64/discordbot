import discord
from discord.ext import commands
import sqlite3
import re

# Init DB
conn = sqlite3.connect('bot.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        event_id INTEGER PRIMARY KEY,
        user_limit INTEGER DEFAULT 0)
''')
conn.commit()



# Discord commands
class EventTracking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    @commands.bot_has_permissions(manage_events=True)
    async def on_scheduled_event_user_add(self, event, member):
        users = 0
        async for user in event.users():
            users += 1
        event_id = event.id
        user_limit = get_user_limit(event_id)
        channel = self.bot.get_channel(1212453511087001690)
        event_name = re.sub("\[.*?\] ", "", event.name)
        if user_limit == 0:
            pass
        elif user_limit < users:
            await member.send(f"""# 🔔 Notification from NYFurs Bot

Dear {member.name},

You're receiving this message because you signed up for an event (**[{event.name}](<{event.url}>)**) that is full. As a result, your RSVP for this event is invalidated and you can't attend the event.

Since Discord doesn't have a way to remove people from signing up from events, please consider un-RSVPing for the event so the host can keep track of members attending the event.

Please consider attending another event that isn't full. Thank you for your understanding!""")
            await event.edit(name = "[FULL] " + event_name)
            await channel.send(f"User {member.mention} has overbooked (**[{event.name}](<{event.url}>)**)")
        elif user_limit == users:
            await event.edit(name = "[FULL] " + event_name)
        elif user_limit > users:
            await event.edit(name = f"[{users}/{user_limit}] " + event_name)

    @commands.Cog.listener()
    @commands.bot_has_permissions(manage_events=True)
    async def on_scheduled_event_user_remove(self, event, member):
        users = 0
        async for user in event.users():
            users += 1
        event_id = event.id
        user_limit = get_user_limit(event_id)
        event_name = re.sub("\[.*?\] ", "", event.name)
        if user_limit == 0:
            pass
        elif user_limit == users or user_limit < users:
            await event.edit(name = "[FULL] " + event_name)
        elif user_limit > users:
            await event.edit(name = f"[{users}/{user_limit}] " + event_name)

    @commands.command()
    @commands.has_permissions(manage_events=True)
    @commands.bot_has_permissions(manage_events=True)
    async def eventlimit(self, ctx, event: discord.ScheduledEvent, user_limit: int):
        event_id = event.id
        set_user_limit(event_id, user_limit)
        event_name = re.sub("\[.*?\] ", "", event.name)
        if user_limit == 0:
            await event.edit(name = event_name)
            await ctx.send(f"The event `{event.name}` now has the user limit removed")
        elif user_limit > 0:
            users = 0
            async for user in event.users():
                users += 1
            await event.edit(name = f"[{users}/{user_limit}] " + event_name)
            await ctx.send(f"The event `{event.name}` now has the user limit set to `{user_limit}`")
        else:
            await ctx.send("Invalid limit")
        print(get_user_limit(event_id))

        
# Functions to control the DB
def get_user_limit(event_id):
    cursor.execute('SELECT user_limit FROM events WHERE event_id = ?', (event_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def set_user_limit(event_id, user_limit):
    cursor.execute('INSERT OR REPLACE INTO events (event_id, user_limit) VALUES (?, ?)', (event_id, user_limit))
    conn.commit()


async def setup(bot):
    await bot.add_cog(EventTracking(bot))

print("Initialized event tracking cog")