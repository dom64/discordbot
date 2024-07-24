import discord
from discord.ext import commands
import sqlite3
from typing import Union

import discord.ext
import discord.ext.commands

#Init DB
conn = sqlite3.connect('db/bot.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        guild_id INTEGER PRIMARY KEY,
        auto_create_event INTEGER DEFAULT 0,
        auto_archive_event INTEGAR DEFAULT 0,
        auto_delete_event BOOL DEFAULT 0)
''')
conn.commit()

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        print("Initialized settings cog")

    @commands.group(invoke_without_command=True, aliases=['setting'])
    @commands.has_permissions(manage_guild=True)
    async def settings(self, ctx):
        await ctx.send("""Here are all the settings:
auto_create_event
auto_delete_event
auto_archive_event""")

    @settings.command()
    @commands.has_permissions(manage_events=True)
    @commands.bot_has_permissions(manage_events=True, manage_roles=True)
    async def auto_create_event(self, ctx, choice: Union[discord.TextChannel, int] = None):
        if choice is None:
            await ctx.send("auto_create_event (0/#channel): This setting allows you to set a text channel to automatically put newly made events in. Set to 0 to disable")
            return
        
        if isinstance(choice, discord.TextChannel):
            auto_create_event_db(ctx.guild.id, choice.id)
            await ctx.send(f"Setting is now set to {choice.mention}")
            return

        if isinstance(choice, int) and choice == 0:
            auto_create_event_db(ctx.guild.id, choice)
            await ctx.send("Setting is now disabled!")
            return
        
        await ctx.send("Invalid input")

    @settings.command()
    @commands.has_permissions(manage_events=True)
    @commands.bot_has_permissions(manage_events=True, manage_roles=True)
    async def auto_delete_event(self, ctx, choice: bool = None):
        if choice is None:
            await ctx.send("auto_delete_event (true/false): This setting allows you to automatically delete an event once it is over.")
            return
        
        if choice is True:
            auto_delete_event_db(ctx.guild.id, choice)
            await ctx.send("Setting is now enabled!")
            return
        if choice is False:
            auto_delete_event_db(ctx.guild.id, choice)
            await ctx.send("Setting is now disabled!")
            return
        
    @settings.command()
    @commands.has_permissions(manage_events=True)
    @commands.bot_has_permissions(manage_events=True, manage_roles=True)
    async def auto_archive_event(self, ctx, choice: Union[discord.TextChannel, int] = None):
        if choice is None:
            await ctx.send("auto_archive_event (0/#channel): This setting allows you to set a text channel to automatically archive finished events. Set to 0 to disable. (NOTE: auto delete has to be enabled in order for this to work!!!)")
            return
        
        if isinstance(choice, discord.TextChannel):
            auto_archive_event_db(ctx.guild.id, choice.id)
            await ctx.send(f"Setting is now set to {choice.mention}")
            return

        if isinstance(choice, int) and choice == 0:
            auto_archive_event_db(ctx.guild.id, choice)
            await ctx.send("Setting is now disabled!")
            return
        
        await ctx.send("Invalid input")
            

    async def cog_command_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.BadUnionArgument):
            await ctx.send("Invalid input")
        elif isinstance(error, discord.ext.commands.errors.BadBoolArgument):
            await ctx.send("Invalid input. This setting only uses true and false")
        else:
            raise error


def auto_create_event_db(guild_id, auto_create_event):
    cursor.execute('INSERT OR IGNORE INTO settings (guild_id, auto_create_event) VALUES (?, ?)', (guild_id, auto_create_event))
    cursor.execute('UPDATE settings SET auto_create_event=? WHERE guild_id=?', (auto_create_event, guild_id))
    conn.commit()

def auto_delete_event_db(guild_id, auto_delete_event):
    cursor.execute('INSERT OR IGNORE INTO settings (guild_id, auto_delete_event) VALUES (?, ?)', (guild_id, auto_delete_event))
    cursor.execute('UPDATE settings SET auto_delete_event=? WHERE guild_id=?', (auto_delete_event, guild_id))
    conn.commit()

def auto_archive_event_db(guild_id, auto_archive_event):
    cursor.execute('INSERT OR IGNORE INTO settings (guild_id, auto_archive_event) VALUES (?, ?)', (guild_id, auto_archive_event))
    cursor.execute('UPDATE settings SET auto_archive_event=? WHERE guild_id=?', (auto_archive_event, guild_id))
    conn.commit()


async def setup(bot):
    await bot.add_cog(Settings(bot))