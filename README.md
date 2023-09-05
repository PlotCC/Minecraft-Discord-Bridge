# Bridge Bot
This is a somewhat advanced bridge bot that combines the functionality of a
Minecraft <-> Discord bridge with some other utilities like automatic server
restarts and whatnot.

This opens a 3-window tmux session where one window is the debug output of the
bot, one window is the server console, and one window is the webhook bridge.

## Usage
Go through the configuration, and tune to your liking. Most things can be left
alone, but names of things can be changed (be sure to set the `latest.log`
location, webhook url, bot token, and channel ID correctly!). 

Then, once you've done all that. Just `python3 bot.py` (I will add a shebang or
whatever it's called once I remember or google how to do it).

## Features
Current feature list:

- Webhook for Minecraft --> Discord communication.
- Tmux setup to look fancy.
- Starts the minecraft server for you.
- Bot that just echoes "Bruh"

Planned feature list:

- [x] [Requirement: Send messages from Discord to Minecraft (#1)](https://github.com/PlotCC/Minecraft-Discord-Bridge/issues/1)
- [x] [Requirement: Fancify the output in both Minecraft and Discord (#2)](https://github.com/PlotCC/Minecraft-Discord-Bridge/issues/2)
- [x] [Requirement: Autmatic Minecraft Reboots (#3)](https://github.com/PlotCC/Minecraft-Discord-Bridge/issues/3)
- [x] [Nice-to-have: `/list` / `/online` command to get currently online users (#4)](https://github.com/PlotCC/Minecraft-Discord-Bridge/issues/4)
- [ ] [Nice-to-have: More events detected (deaths, advancements, ...) (#5)](https://github.com/PlotCC/Minecraft-Discord-Bridge/issues/5)
- [ ] [Nice-to-have: Minecraft/Discord nickname linking (#6)](https://github.com/PlotCC/Minecraft-Discord-Bridge/issues/6)

## Python pip modules installation string
```
pip install -U discord.py libtmux zmq minecraftTellrawGenerator asyncio aiohttp requests tzdata emoji
```
**Note:** If you are running python version below 3.9, you will need to install `backports.zoneinfo` as well.