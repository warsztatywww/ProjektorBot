#!/usr/bin/env python3
import discord
import time
import os
import random
import json
import re
import asyncio

MEME_DIR = os.getenv("MEME_DIR", "./memes")
projector_channel = None
projector_task = None
projector_msg = None
turnoff_msg = None
turnoff_task = None

def wordsearch(word: str, msg: str, flags: int = re.I) -> bool:
    return re.search(r'\b' + word + r'\b', msg, flags) is not None

client = discord.Client()

async def projector(init_delay=10):
    global projector_channel, projector_msg
    await asyncio.sleep(init_delay)
    while True:
        meme = os.path.join(MEME_DIR, random.choice(os.listdir(MEME_DIR)))
        react = None
        time = 15
        if random.random() < 0.1:
            meme = "./quack.mp4-q38Y5FLK63k.mp4"
            react = "🦆"
        elif random.random() < 0.025:
            meme = os.path.join("./farmio", random.choice(os.listdir("./farmio")))
            react = "🥚"
            time = 60
        if projector_msg:
            await projector_msg.delete()
        projector_msg = await projector_channel.send(file=discord.File(meme))
        await projector_msg.add_reaction(discord.utils.get(projector_channel.guild.emojis, name='projector_power'))
        if react:
            await projector_msg.add_reaction(react)
        await asyncio.sleep(time)

async def turnoff(channel):
    global turnoff_msg, turnoff_task
    turnoff_msg = await channel.send(file=discord.File('projector_confirm.jpg'))
    await turnoff_msg.add_reaction(discord.utils.get(projector_channel.guild.emojis, name='projector_power'))
    await turnoff_msg.add_reaction(discord.utils.get(projector_channel.guild.emojis, name='projector_any'))
    await asyncio.sleep(10)
    await turnoff_msg.delete()
    turnoff_msg = None
    turnoff_task = None

async def turnoff_beep(channel):
    msg = await channel.send('*BEEP* *BEEP*')
    await asyncio.sleep(5)
    await msg.delete()

async def poweroff_button(channel):
    global turnoff_task, turnoff_msg, projector_channel, projector_task, projector_msg
    if not turnoff_task:
        turnoff_task = asyncio.create_task(turnoff(channel))
    else:
        turnoff_task.cancel()
        turnoff_task = None
        await turnoff_msg.delete()
        turnoff_msg = None
        asyncio.create_task(turnoff_beep(channel))

        projector_channel = None
        projector_task.cancel()
        projector_task = None
        if projector_msg:
            await projector_msg.delete()
            projector_msg = None

        await client.change_presence(status=discord.Status.idle, activity=discord.Game(name='Czekanie na memy'))

async def power_button(message):
    global projector_channel, projector_msg, projector_task
    if not projector_channel:
        projector_channel = message.channel
        projector_msg = await message.channel.send(file=discord.File('bootscreen.gif'))
        projector_task = asyncio.create_task(projector())
        await client.change_presence(status=discord.Status.online, activity=discord.Game(name='📽️ Włączony!'))
    elif projector_channel != message.channel:
        await message.channel.send('Przed przeniesieniem projektora do innego pokoju musisz go odłączyć od prądu...')
    else:
        await poweroff_button(message.channel)
    await message.delete()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(status=discord.Status.idle, activity=discord.Game(name='Czekanie na memy'))

@client.event
async def on_reaction_add(reaction, user):
    global turnoff_msg, turnoff_task, projector_msg
    if user == client.user:
        return
    if projector_msg and reaction.message.id == projector_msg.id and isinstance(reaction.emoji, discord.Emoji) and reaction.emoji.name == 'projector_power':
        await reaction.remove(user)
        await poweroff_button(reaction.message.channel)
    if turnoff_msg and reaction.message.id == turnoff_msg.id and isinstance(reaction.emoji, discord.Emoji) and reaction.emoji.name == 'projector_power':
        await reaction.remove(user)
        await poweroff_button(reaction.message.channel)
    if turnoff_msg and reaction.message.id == turnoff_msg.id and isinstance(reaction.emoji, discord.Emoji) and reaction.emoji.name == 'projector_any':
        turnoff_task.cancel()
        turnoff_task = None
        await turnoff_msg.delete()
        turnoff_msg = None

@client.event
async def on_message(message):
    global projector_channel, projector_task, projector_msg, turnoff_msg, turnoff_task

    if message.author == client.user:
        return

    sent_meme = False
    
    if "kaczki" in message.content.lower():
        await message.add_reaction("🦆")
        if client.user in message.mentions:
            msg = await message.channel.send(file=discord.File("./quack.mp4-q38Y5FLK63k.mp4"))
            await msg.add_reaction("🦆")
            sent_meme = True
            
    if any(wordsearch(w, message.content) for w in ('kurki', 'kurkom', 'jajka', 'farmio', 'kur', 'GMO')):
        await message.add_reaction("🥚")
        if client.user in message.mentions:
            msg = await message.channel.send(file=discord.File(os.path.join("./farmio", random.choice(os.listdir("./farmio")))))
            await msg.add_reaction("🥚")
            sent_meme = True
    
    if sent_meme:
        return

    if message.channel.type is discord.ChannelType.private:
        print('SECURITY NOTICE: {} tried to steal the PROJEKTOR'.format(message.author))
        await message.channel.send('{0.mention} is not in the sudoers file. This incident will be reported.'.format(message.author))
        root = client.get_user(202109224191393792) # krzys_h#0051
        await root.send('{0} jest zlodziejem :gun:'.format(message.author))
        return

    if client.user in message.mentions:
        if any(wordsearch(w, message.content) for w in ('włącz', 'wyłącz', 'on', 'off', 'power', 'zasilanie', 'włącznik')):
            await power_button(message)
        else:
            await message.channel.send('gdzie mi z tymi paluchami brudnymi od tostów do projektora')

    if message.channel.name == "memy":
        emojis = re.finditer(r'<:(\w*):(\d*)>', message.content)
        if any(emoji[1] == "projector_power" for emoji in emojis):
            await power_button(message)

        for attach in message.attachments:
            if attach.filename.startswith("quack"):
                await message.add_reaction("🦆")
                await message.channel.send("{0.mention} wszystko fajnie ale dosyć tych kaczek".format(message.author))
            elif attach.width and attach.height:
                with open(os.path.join(MEME_DIR, "DISCORD_{}_{}".format(attach.id, attach.filename)), "wb") as f:
                    await attach.save(f)
                await message.add_reaction("🎺")
                await message.channel.send('@here :trumpet: NOWY MEM :trumpet:', tts=True)
                if projector_task:
                    projector_task.cancel()
                    if projector_msg:
                        await projector_msg.delete()
                        projector_msg = None
                    projector_task = asyncio.create_task(projector(30))

client.run(os.environ['DISCORD_TOKEN'])
