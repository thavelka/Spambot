import os
from os import path
from datetime import datetime
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from shutil import copyfile


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')
PREFIX = 's!'

# Client declaration
bot = commands.Bot(command_prefix=('s!', 'S!', 'alexa ', 'Alexa ', 'ALEXA '), case_insensitive = True)

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
async def play(ctx, query, *effects):
    """Plays a file from the guild's sounds folder. Format: `s!play {name} [bb, fast, slow, echo, robot, loop, reverse](optional)`"""
    filepath = f'sounds/{ctx.guild.id}/{query.lower()}.mp3'
    if not path.exists(filepath):
        await ctx.send(f'Sound {query} not found')
    else:
        if effects and len(effects) > 0:
            inpath = f'sounds/{ctx.guild.id}/.in.mp3'
            outpath = f'sounds/{ctx.guild.id}/.tmp.mp3'
            copyfile(filepath, outpath)
            for effect in effects:
                copyfile(outpath, inpath)
                if effect == "bb":
                    os.system(f'ffmpeg -y -i {inpath} -filter_complex "acrusher=level_in=4:level_out=10:bits=8:mode=log:aa=1" -f mp3 - | ffmpeg -y -i - -filter "bass=g=14:f=150" {outpath}')
                elif effect == "fast":
                    os.system(f'ffmpeg -y -i {inpath} -af asetrate=22050*1.5,aresample=22050 {outpath}')
                elif effect == "slow":
                    os.system(f'ffmpeg -y -i {inpath} -af asetrate=22050*0.6,aresample=22050 {outpath}')
                elif effect == "echo":
                    os.system(f'ffmpeg -y -i {inpath} -af aecho=0.9:0.6:200:1 {outpath}')
                elif effect == "robot":
                    os.system(f'ffmpeg -y -i {inpath} -af afftfilt="real=\'hypot(re,im)*sin(0)\':imag=\'hypot(re,im)*cos(0)\':win_size=512:overlap=0.75" {outpath}')
                elif effect == "loop":
                    os.system(f'ffmpeg -y -i {inpath} -af aloop=5:size=22050*3 {outpath}')
                elif effect == "reverse":
                    os.system(f'ffmpeg -y -i {inpath} -af areverse {outpath}')
            filepath = outpath

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(filepath))
        ctx.voice_client.play(source, after=lambda e:print('Player error: %s' % e) if e else None)


@bot.event
async def on_voice_state_update(member, before, after):
    # Leave after last person leaves VC
    if before.channel is not None and after.channel is None:
        if len(before.channel.members) <= 2:
            voice_client = member.guild.voice_client
            if voice_client is not None:
                await voice_client.disconnect()
    # Play sound if user is joining VC
    elif before.channel is None and after.channel is not None:
        intro_dict = get_intro_dict(member.guild)

        # Check if user has intro sound set
        sound = intro_dict.get(str(member.id))
        if not sound:
            return

        # Check if sound file exists
        filepath = f'sounds/{member.guild.id}/{sound}.mp3'
        if not path.exists(filepath):
            return

        # Connect to voice channel if not connected, stop if already playing
        voice_client = member.guild.voice_client
        if voice_client is None:
            if member.voice:
                await member.voice.channel.connect()
        elif voice_client.is_playing():
            voice_client.stop()
        voice_client = member.guild.voice_client
        if not voice_client:
            return

        # Play the sound
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(filepath))
        voice_client.play(source, after=lambda e:print('Player error: %s' % e) if e else None)

@bot.command()
async def upload(ctx, *, name):
    name = name.lower().strip()
    """Uploads a sound file. Format: `s!upload {name}` plus attachment"""
    if not ctx.message.attachments:
        await ctx.send("Attachment required")
    elif not name:
        await ctx.send("Name is required")
    elif len(name.split()) > 1:
        await ctx.send("Name must be one word")
    elif path.exists(f'./sounds/{ctx.guild.id}/{name}.mp3'):
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
        os.system(f'ffmpeg -i {tmp} -ab 48k -ac 1 -ar 22050 -to 00:00:59 ./sounds/{ctx.guild.id}/{name}.mp3')
        os.system(f'rm {tmp}')
        await ctx.send(f'Uploaded {name}')


@bot.command()
async def list(ctx):
    """Lists sounds in the guild's directory"""
    if path.exists(f'sounds/{ctx.guild.id}'):
        files = os.listdir(f'sounds/{ctx.guild.id}')
        if len(files) == 0:
            await ctx.send('Sounds directory is empty. Type s!help to see how to upload new sound files.')
        else:
            files.sort()
            mp3s = [x.split(".")[0] for x in files if ".mp3" in x and x[0] != "."]
            string_buffer = ""
            for name in mp3s:
                if len(string_buffer) == 0:
                    string_buffer = name
                elif len(string_buffer) + len(name) + 2 < 2000:
                    string_buffer = ', '.join((string_buffer, name))
                else:
                    await ctx.send(string_buffer)
                    string_buffer = name
            await ctx.send(string_buffer)


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
    """Set intro sound to play when you enter voice chat. Format: `s!setintro {name}`"""
    name = name.lower().strip()
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
        intro_dict[str(ctx.author.id)] = name
        save_intro_dict(ctx.guild, intro_dict)
        await ctx.send(f'Set {name} as intro sound for {ctx.author.name}.')

@bot.command()
async def clearintro(ctx):
    """Removes intro sound for user"""
    intro_dict = get_intro_dict(ctx.guild)
    del intro_dict[str(ctx.author.id)]
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
            f.write(f'{k} {v}\n')


# Run
bot.run(TOKEN)
