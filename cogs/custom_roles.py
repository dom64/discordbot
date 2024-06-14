import discord
from discord.ext import commands
import sqlite3
from typing import Union

# Notes
# For one time use items 0 = doesnt have never used 1 = does have never used 2 = used
# For unlocks use 0 = doesnt have 1 = does have
# For multi use number is just how much they have

#Init DB
conn = sqlite3.connect('bot.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS custom_roles (
        user_id INTEGER PRIMARY KEY,
        role_id INTEGER DEFAULT 0)
''')
conn.commit()

class Customroles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        print("Initialized custom_roles cog")

    @commands.group(invoke_without_command=True, aliases=['customrole'])
    async def customroles(self, ctx, name: str = None, color: discord.Colour = None):
        if name is None:
            await ctx.send('!customroles (name) (color hex code)\nExample: !customroles swagmaster #4fa334\nExample: !customroles water blue\nExample: !customroles "boring role" default')
            return
        user_id = ctx.author.id
        user_eligible = check_custom_role_eligible(user_id)
        if user_eligible == 0:
            await ctx.send("You never purchased this. Please go to the shop and purchase this.")
            return
        role_id = check_custom_role(user_id)
        name = name[:100]
        if role_id == 0:
            if color is None:
                role = await ctx.guild.create_role(name=name)
            else:
                role = await ctx.guild.create_role(name=name, color=color)
            await ctx.author.add_roles(role)
            set_custom_role(user_id, role.id)
        else:
            role = discord.utils.get(ctx.guild.roles, id=role_id)
            if color is None:
                await role.edit(name=name)
            else:
                await role.edit(name=name, colour=color)
        await ctx.send("Role has been set")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.BadColourArgument):
            await ctx.send("Invalid color")
        else:
            raise error


def check_custom_role_eligible(user_id):
    cursor.execute('SELECT custom_role FROM shop WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def check_custom_role(user_id):
    cursor.execute('SELECT role_id FROM custom_roles WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def set_custom_role(user_id, role_id):
    cursor.execute('INSERT OR IGNORE INTO custom_roles (user_id, role_id) VALUES (?, ?)', (user_id, role_id))
    conn.commit()

async def setup(bot):
    await bot.add_cog(Customroles(bot))
