import discord
from discord.ext import commands
import sqlite3
import random
import datetime
from typing import Union

# Init DB
conn = sqlite3.connect('db/bot.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS economy (
        user_id INTEGER PRIMARY KEY,
        cash INTEGER DEFAULT 0,
        daily INTEGER DEFAULT 0)
''')
conn.commit()

# Discord commands
class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_load(self):
        print("Initialized economy cog")

    @commands.command(aliases=['balance', 'bal', "$", "money"])
    async def cash(self, ctx, target: discord.Member = None):
        target = target or ctx.author
        user_id = target.id
        cash = get_cash(user_id)
        await ctx.send(f'{target.mention} has ${cash}')

    @cash.error
    async def cash_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.MemberNotFound):
            await ctx.send("Error: Member not found")
        else:
            raise error

    @commands.command(aliases=['flip', 'coinflip'])
    async def betflip(self, ctx, amount: str = None, choice: str = 'h'):
        if amount is None:
            await ctx.send("!betflip (amount) (h/t)")
            return
        user_id = ctx.author.id
        user_cash = get_cash(user_id)

        if amount.lower() == 'all':
            amount = user_cash
        else:
            try:
                amount = int(amount)
            except ValueError:
                await ctx.send("You didn't put a valid number")
                return
        
        if amount > user_cash:
            await ctx.send("Don't have enough money broke-ass")
            return
        if amount <= 0:
            await ctx.send("You can't bet nothing")
            return
        
        choice = choice[0].lower()
        if choice not in ['h', 't']:
            await ctx.send("Not a valid option")
            return
        result = random.choice(['h', 't'])

        if result == choice:
            add_money_to_user(user_id, amount)
            await ctx.send(f"Congrats you won {amount} coins!!!!!")
        else:
            remove_money_to_user(user_id, amount)
            await ctx.send(f"Congrats you lost {amount} coins!!!!!")

    @commands.command()
    async def daily(self, ctx):
        user_id = ctx.author.id
        last_timestamp = get_daily(user_id)
        current_timestamp = int(datetime.datetime.now().timestamp())
        cooldown = 21600 # 6 hours in seconds
        time_left = cooldown - (current_timestamp - last_timestamp)

        if time_left <= 0:
            change_daily(user_id, current_timestamp)
            add_money_to_user(user_id, 100)
            await ctx.send("Here is your $100 bitch!")
        else:
            time_left_msg = str(datetime.timedelta(seconds=time_left))
            await ctx.send(f"You've claimed your check come back in {time_left_msg}")

    @commands.command(aliases=['top10'])
    async def top(self, ctx):
        top_ten = get_top()
        embed = discord.Embed(title="Top 10:")

        for x in top_ten:
            member = self.bot.get_user(x[0])
            if member is None:
                member = await self.bot.fetch_user(x[0])
            embed.add_field(name=f"{member.display_name}", value=f"${x[1]}")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def addmoney(self, ctx, target: Union[discord.Member, str], amount: int):
        if isinstance(target, discord.Member):
            user_id = target.id
            add_money_to_user(user_id, amount)
            await ctx.send(f'{target.mention} ${amount} has been added')
        
        elif target.lower() == 'all':
            for member in ctx.guild.members:
                if member.bot:
                    continue
                user_id = member.id
                add_money_to_user(user_id, int(amount))
            await ctx.send(f'Added ${amount} to everypony!')
        
        else:
            await ctx.send("Invalid person")

    @commands.command()
    @commands.is_owner()
    async def rmmoney(self, ctx, target: Union[discord.Member, str], amount: int):
        if isinstance(target, discord.Member):
            user_id = target.id
            remove_money_to_user(user_id, amount)
            await ctx.send(f'{target.mention} ${amount} has been removed')
        
        elif target.lower() == 'all':
            for member in ctx.guild.members:
                if member.bot:
                    continue
                user_id = member.id
                remove_money_to_user(user_id, int(amount))
            await ctx.send(f'Removed ${amount} to everypony!')
        
        else:
            await ctx.send("Invalid person")

    @commands.command(aliases=['dailyreset'])
    @commands.is_owner()
    async def resetdaily(self, ctx, target: Union[discord.Member, str]):
        if isinstance(target, discord.Member):
            user_id = target.id
            change_daily(user_id, 0)
            await ctx.send(f'{target.mention} daily timer reset!')
        
        elif target.lower() == 'all':
            for member in ctx.guild.members:
                if member.bot:
                    continue
                user_id = member.id
                change_daily(user_id, 0)
            await ctx.send(f'Reset daily timer for everypony!')
        
        else:
            await ctx.send("Invalid person")


# Functions to control the DB
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

def get_daily(user_id):
    cursor.execute('SELECT daily FROM economy WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def change_daily(user_id, timestamp):
    cursor.execute('INSERT OR IGNORE INTO economy (user_id, daily) VALUES (?, ?)', (user_id, timestamp))
    cursor.execute('UPDATE economy SET daily=? WHERE user_id=?', (timestamp, user_id))
    conn.commit()

def get_top():
    cursor.execute("SELECT * FROM economy ORDER BY cash DESC LIMIT 10")
    result = cursor.fetchall()
    return result if result else 0

async def setup(bot):
    await bot.add_cog(Economy(bot))