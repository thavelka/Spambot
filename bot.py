import os
from os import path
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')
PREFIX = 's!'

# Client declaration
bot = commands.Bot(command_prefix='s!')

@bot.event
async def on_ready():
    print('Logged on as {0}!'.format(bot.user))
    if not path.exists('sounds'):
        os.mkdir('sounds')
    if not path.exists('sounds/tmp'):
        os.mkdir('sounds/tmp')
    for guild in bot.guilds:
        if not path.exists(f'sounds/{guild.id}'):
            os.mkdir('sounds/{guild.id}')
@bot.event
async def on_guild_join(guild):
    print(f'Joined guild: {guild.name}')
    if not path.exists(f'sounds/{guild.id}'):
        os.mkdir('sounds/{guild.id}')

@bot.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'{datetime.now().date()} - {datetime.now().time()}\n')
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise


@bot.command()
async def play(ctx, *, query):
    """Plays a file from the guild's sounds folder. Format: `s!play {name}`"""
    filepath = f'./sounds/{ctx.guild.id}/{query}.mp3'
    if not path.exists(filepath):
        await ctx.send(f'Sound {query} not found')
    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(filepath))
    ctx.voice_client.play(source, after=lambda e:print('Player error: %s' % e) if e else None)
    await asyncio.sleep(30)
    if ctx.voice_client and not ctx.voice_client.is_playing():
        await ctx.voice_client.disconnect()

@bot.command()
async def upload(ctx, *, name):
    """Uploads a sound file. Format: `s!upload {name}` plus attachment"""
    if not ctx.message.attachments:
        await ctx.send("Attachment required")
    elif not name:
        await ctx.send("Name is required")
    elif len(name.split()) > 1:
        await ctx.send("Name must be one word")
    elif path.exists(f'./sounds/{ctx.guild.id}/{name.strip()}.mp3'):
        await ctx.send(f'A sound with name {name} already exists')
    else:
        attachment = ctx.message.attachments[0]
        components = attachment.filename.split('.')
        if len(components) < 2:
            await ctx.send('File type could not be determined')
            return
        elif components[1].lower() not in ['mp3', 'm4a', 'ogg', 'wav', 'flac', 'mp4', 'mkv', 'webm']:
            await ctx.send('Unsupported file type')
            return
        tmp = f'./sounds/tmp/{attachment.filename}'
        print(tmp)
        await attachment.save(tmp)
        os.system(f'ffmpeg -i {tmp} -ab 48k -ac 1 -ar 22050 -to 00:00:29 ./sounds/{ctx.guild.id}/{name.strip()}.mp3')
        os.system(f'rm {tmp}')
        await ctx.send(f'Uploaded {name.strip()}')

@bot.command()
async def list(ctx):
    """Lists sounds in the guild's directory"""
    if path.exists(f'sounds/{ctx.guild.id}'):
        files = os.listdir(f'sounds/{ctx.guild.id}')
        if len(files) == 0:
            await ctx.send('Sounds directory is empty. Type s!help to see how to upload new sound files.')
        else:
            files.sort()
            await ctx.send(', '.join(files))

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
