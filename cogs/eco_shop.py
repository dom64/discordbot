import discord
from discord.ext import commands
import sqlite3

# Notes
# For one time use items 0 = doesnt have never used 1 = does have never used 2 = used
# For unlocks use 0 = doesnt have 1 = does have
# For multi use number is just how much they have

#Init DB
conn = sqlite3.connect('db/bot.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS shop (
        user_id INTEGER PRIMARY KEY,
        custom_role BOOL DEFAULT 0)
''')
conn.commit()

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        print("Initialized shop cog")

    @commands.group(invoke_without_command=True)
    async def shop(self, ctx):
        embed = discord.Embed(title="Shop", description="Use !shop buy # to purchase items")
        embed.add_field(name=f"1️⃣ Custom role", value=f"$250")
        await ctx.send(embed=embed)

    @shop.command()
    async def buy(self, ctx, item = None):
        if item is None or not item.isdecimal():
            await ctx.send("Please choose a number")
            return
        if item == "1":
            already_has = custom_role(ctx.author.id)
            if already_has == 1:
                await ctx.send("You already bought this")
                return
            if already_has == 0:
                await ctx.send("You have custom roles unlocked! Use the !customroles command to make ur own role.")
                return
            if already_has == 2:
                await ctx.send("You don't have enough money to purchase this")
            else:
                await ctx.send("Unknown error")
                return


    async def cog_command_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.MemberNotFound):
            await ctx.send("Error: Member not found")
        else:
            raise error

def get_cash(user_id):
    cursor.execute('SELECT cash FROM economy WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def add_money_to_user(user_id, amount):
    current_cash = get_cash(user_id)
    new_cash = current_cash + amount
    cursor.execute('INSERT OR IGNORE INTO economy (user_id, cash) VALUES (?, ?)', (user_id, new_cash))
    cursor.execute('UPDATE economy SET cash=? WHERE user_id=?', (new_cash, user_id))
    conn.commit()

def remove_money_to_user(user_id, amount):
    current_cash = get_cash(user_id)
    new_cash = current_cash - amount
    cursor.execute('INSERT OR IGNORE INTO economy (user_id, cash) VALUES (?, ?)', (user_id, new_cash))
    cursor.execute('UPDATE economy SET cash=? WHERE user_id=?', (new_cash, user_id))
    conn.commit()

def custom_role(user_id):
    cursor.execute('SELECT custom_role FROM shop WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result != None:
        return 1
    cash = get_cash(user_id)
    if cash < 250:
        return 2
    remove_money_to_user(user_id, 250)
    cursor.execute('INSERT OR IGNORE INTO shop (user_id, custom_role) VALUES (?, ?)', (user_id, 1))
    cursor.execute('UPDATE shop SET custom_role=? WHERE user_id=?', (1, user_id))
    conn.commit()
    return 0

async def setup(bot):
    await bot.add_cog(Shop(bot))
