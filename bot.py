import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')
PREFIX = 's!'

# Client declaration
bot = commands.Bot(command_prefix='s!')

@bot.event
async def on_ready():
    print('Logged on as {0}!'.format(bot.user))


@bot.command()
async def play(ctx, name):
    await ctx.send(f'Playing {name}')


# Run
bot.run(TOKEN)
