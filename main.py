import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.all()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def setup():
    for f in os.listdir("./cogs"):
	    if f.endswith(".py"):
		    await bot.load_extension("cogs." + f[:-3])

async def main():
    await setup()
    await bot.start("MTIxMzU4MjIzNDczMzI1MjY1OQ.GMRHzd.pI1bjQHUhrWiaH7f0eCZ4w3TWXBuEtSuV5G_Zw")

asyncio.run(main())