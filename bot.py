# Discord bot to act as a bridge between MC servers.

import discord

import config

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    channel = client.get_channel(config.bot["channel_id"]) 
    await channel.send("Bridge started.")

@client.event
async def on_message(message):
    print(f"Received message: {message}")
    if message.author == client.user:
        return
            
    if message.channel.id != config.bot["channel_id"]:
        return
            
    if message.content == "bruh" or message.content == "Bruh":
        await message.channel.send("Bruh")


if __name__ == "__main__":
    client.run(config.bot["token"])

    print("Dude has stopped bro")
