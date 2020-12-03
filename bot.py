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


@bot.command()
async def play(ctx, *, query):
    """Plays a file from the local filesystem"""
    path = f'./sounds/{query}.mp3'
    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(path))
    ctx.voice_client.play(source, after=lambda e:print('Player error: %s' % e) if e else None)
    await asyncio.sleep(30)
    if ctx.voice_client and not ctx.voice_client.is_playing():
        await ctx.voice_client.disconnect()

async def stop(ctx):
    await ctx.voice_client.disconnect()

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
