import os
from os import path
from datetime import datetime
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


@bot.event
async def on_ready():
    print('Logged on as {0}!'.format(bot.user))
    if not path.exists('sounds'):
        os.mkdir('sounds')
    if not path.exists('sounds/tmp'):
        os.mkdir('sounds/tmp')
    for guild in bot.guilds:
        if not path.exists(f'sounds/{guild.id}'):
            os.mkdir(f'sounds/{guild.id}')


@bot.event
async def on_guild_join(guild):
    print(f'Joined guild: {guild.name}')
    if not path.exists(f'sounds/{guild.id}'):
        os.mkdir(f'sounds/{guild.id}')


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
    filepath = f'sounds/{ctx.guild.id}/{query}.mp3'
    if not path.exists(filepath):
        await ctx.send(f'Sound {query} not found')
    else:
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(filepath))
        ctx.voice_client.play(source, after=lambda e:print('Player error: %s' % e) if e else None)
        await asyncio.sleep(62)
    if ctx.voice_client and not ctx.voice_client.is_playing():
        await ctx.voice_client.disconnect()


# @bot.event
# async def on_voice_state_update(member, before, after):
#     print("onvoicestateupdate")
#     # if before.channel is None and after.channel is not None:
#     intro_dict = get_intro_dict(member.guild)
#     sound = intro_dict.get(member.id)
#     if sound:
#         print("playing", sound)
#         await bot.invoke(bot.get_command('play'), sound)


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
        os.system(f'ffmpeg -i {tmp} -ab 48k -ac 1 -ar 22050 -to 00:00:59 ./sounds/{ctx.guild.id}/{name.strip()}.mp3')
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


@bot.command()
async def delete(ctx, *, name):
    """Deletes specified sound from the guild's directory"""
    if not name:
        await ctx.send("Name is required")
        return
    if len(name.split()) > 1:
        await ctx.send("Name must be one word")
        return
    filepath = f'sounds/{ctx.guild.id}/{name.strip()}.mp3'
    if not path.exists(filepath):
        await ctx.send(f'Sound {name} not found.')
    else:
        os.remove(filepath)
        await ctx.send(f'Deleted sound {name}.')

@bot.command()
async def setintro(ctx, *, name):
    """Set intro sound to play when you enter voice chat"""
    if not name:
        await ctx.send("Name is required")
        return
    if len(name.split()) > 1:
        await ctx.send("Name must be one word")
        return
    filepath = f'sounds/{ctx.guild.id}/{name.strip()}.mp3'
    if not path.exists(filepath):
        await ctx.send(f'Sound {name} not found.')
    else:
        intro_dict = get_intro_dict(ctx.guild)
        intro_dict[ctx.author.id] = name
        save_intro_dict(ctx.guild, intro_dict)
        await ctx.send(f'Set {name} as intro sound for {ctx.author.name}.')

@bot.command()
async def clearintro(ctx):
    """Removes intro sound for user"""
    intro_dict = get_intro_dict(ctx.guild)
    del intro_dict[ctx.user.id]
    save_intro_dict(ctx.guild, intro_dict)
    await ctx.send(f'Removed intro sound for {ctx.author.name}.')


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


def get_intro_dict(guild):
    """Returns dictionary containing users' intro sounds from file"""
    filepath = f'sounds/{guild.id}/intros.txt'
    if path.exists(filepath):
        with open(filepath) as f:
            return dict([line.split() for line in f])
    else:
        return {}


def save_intro_dict(guild, data):
    """Saves guilds intro sounds dictionary back to file"""
    filepath = f'sounds/{guild.id}/intros.txt'
    with open(filepath, 'w') as f:
        for k, v in data.items():
            f.write(f'{k} {v}')


# Run
bot.run(TOKEN)
