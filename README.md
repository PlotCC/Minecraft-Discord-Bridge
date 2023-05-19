# Bridge Bot
This is a somewhat advanced bridge bot, that combines the functionality of a
minecraft<->discord bridge with some other utilities like automatic server
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

- [ ] Bot that sends messages from Discord to Minecraft.
- [ ] Automatic Minecraft reboot (set time, daily, weekly).
- [ ] Fancy colorations of users.
- [ ] Discord/Minecraft user linking?
- [ ] `/online` (alias `/list`) command to determine who is online from Discord.
- [ ] More events detected (deaths, advancements, ...).