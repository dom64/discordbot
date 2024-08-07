import discord
from discord.ext import commands
import os
import asyncio
import json
import logging


intents = discord.Intents.all()
intents.members = True
discord.utils.setup_logging(level=logging.INFO, root=False)

bot = commands.Bot(command_prefix='!', intents=intents)

with open('db/token.json', 'r') as file:
      data = json.load(file)
      token = data.get('token')

async def setup():
    for f in os.listdir("./cogs"):
	    if f.endswith(".py"):
		    await bot.load_extension("cogs." + f[:-3])

async def main():
    await setup()
    await bot.start(token)

if __name__ == '__main__':
    asyncio.run(main())