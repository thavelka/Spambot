import os
import random
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')
PREFIX = 's!'

# Client declaration
bot = commands.Bot(command_prefix='s!')
last_play = None

@bot.event
async def on_ready():
    print('Logged on as {0}!'.format(bot.user))
    os.system('mkdir ./sounds')
    for guild in bot.guilds:
        os.system(f'mkdir ./sounds/{guild.id}')

@bot.event
async def on_guild_join(guild):
    print(f'Joined guild: {guild.name}')
    os.system(f'mkdir ./sounds/{guild.id}')

@bot.command()
async def play(ctx, *, query):
    """Plays a file from the local filesystem"""
    path = f'./sounds/{ctx.guild.id}/{query}.mp3'
    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(path))
    ctx.voice_client.play(source, after=lambda e:print('Player error: %s' % e) if e else None)
    await asyncio.sleep(30)
    if ctx.voice_client and not ctx.voice_client.is_playing():
        await ctx.voice_client.disconnect()

@bot.command()
async def list(ctx):
    """Lists sounds in the guild's directory"""
    stream = os.popen(f'ls ./sounds/{ctx.guild.id}')
    await ctx.send(stream.read())

@play.before_invoke
async def ensure_voice(ctx):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("You are not connected to a voice channel.")
            raise commands.CommandError("Author not connected to a voice channel.")
    elif ctx.voice_client.is_playing():
        ctx.voice_client.stop()

# Run
bot.run(TOKEN)
