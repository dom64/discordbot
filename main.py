import discord
from discord.ext import commands
import sqlite3
import random
import datetime
from typing import Union

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

conn = sqlite3.connect('bot.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS economy (
        user_id INTEGER PRIMARY KEY,
        cash INTEGER DEFAULT 0,
        daily INTEGER DEFAULT 0)
''')
conn.commit()

@bot.event
async def on_ready():
    print(f'Running as {bot.user}')

@bot.event
async def on_message(message):
    print(f'Message from {message.author}: {message.content}')

    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    print(f'Message deleted in #{message.channel}: {message.content}')

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong!")

@bot.command(aliases=['balance', 'bal'])
async def cash(ctx, target: discord.Member = None):
    target = target or ctx.author
    user_id = target.id
    cash = get_cash(user_id)
    await ctx.send(f'{target.mention} has ${cash}')

@bot.command(aliases=['flip', 'coinflip'])
async def betflip(ctx, amount: str, choice: str = 'h'):
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
    if choice.lower() not in ['h', 't']:
        await ctx.send("Not a valid option")
        return
    result = random.choice(['h', 't'])

    if result == choice.lower():
        add_money_to_user(user_id, amount)
        await ctx.send(f"Congrats you won {amount} coins!!!!!")
    else:
        remove_money_to_user(user_id, amount)
        await ctx.send(f"Congrats you lost {amount} coins!!!!!")

@bot.command()
async def daily(ctx):
    user_id = ctx.author.id
    last_timestamp = get_daily(user_id)
    current_timestamp = int(datetime.datetime.now().timestamp())
    cooldown = 6 * 60 * 60
    time_left = cooldown - (current_timestamp - last_timestamp)

    if time_left <= 0:
        change_daily(user_id, current_timestamp)
        add_money_to_user(user_id, 100)
        await ctx.send("Here is your $100 bitch!")
    else:
        time_left_msg = str(datetime.timedelta(seconds=time_left))
        await ctx.send(f"You've claimed your check come back in {time_left_msg}")

@bot.command()
@commands.check(lambda ctx: ctx.author.id == 303884984903532555)
async def addmoney(ctx, target: Union[discord.Member, str], amount: int):
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

@bot.command()
@commands.check(lambda ctx: ctx.author.id == 303884984903532555)
async def rmmoney(ctx, target: Union[discord.Member, str], amount: int):
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


bot.run('MTIxMzU4MjIzNDczMzI1MjY1OQ.GMRHzd.pI1bjQHUhrWiaH7f0eCZ4w3TWXBuEtSuV5G_Zw')