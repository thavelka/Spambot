import os
import discord
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')
PREFIX = 's!'

# Client declaration
client = commands.Bot(command_prefix=PREFIX)

# Events
@client.event
async def on_ready():
    print('Logged on as {0}!'.format(client.user))

@client.event
async def on_message(message):
    if client.user == message.author:
        return
    print('Message from {0.author}: {0.content}'.format(message))

# Commands


# Run
client.run(TOKEN)
