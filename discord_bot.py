# Custom class discord bot.

import discord
from discord.ext import commands
from discord import VoiceChannel, StageChannel, ForumChannel, TextChannel, CategoryChannel, Thread
from discord.abc import PrivateChannel
from typing import Union, Optional
import libtmux

from rcon import Rcon
from webhook_bridge import Bridge

VocalGuildChannel = Union[VoiceChannel, StageChannel]
GuildChannel = Union[VocalGuildChannel, ForumChannel, TextChannel, CategoryChannel]
Channel = Optional[Union[GuildChannel, Thread, PrivateChannel]]

class Channels:
    """
    Class to hold channel-related data.
    """

    notifications: TextChannel
    bridge: TextChannel

    def __init__(self):
        pass



class RconData:
    """
    Class to hold RCON-related data.
    """

    def __init__(self, bot: 'DiscordBot'):
        self.instance: Rcon = Rcon()
        self.connected: bool = False
        self.running: bool = False
        self.bot: DiscordBot = bot
        
    
    # Function to send a command to the server console, to be used by cogs rather than invoking the console directly.
    async def send_server_command(self, command: str):
        """
        Send a command to the console. This fails if the server is offline.
        """
        if not self.running:
            raise Exception("Server is offline, cannot send command to server console.")
        
        # bot.console_pane.send_keys(command)
        return await self.instance.send(command)



    # Function to send a command to the console, to be used by cogs rather than invoking the console directly.
    def send_console_command(self, command: str):
        """
        Send a command to the console. This fails if the server is online.
        """
        if self.running:
            raise Exception("Server is online, cannot send command to console.")
        
        self.bot.tmux.console_pane.send_keys(command)



class TmuxData:
    """
    Class to hold tmux-related data.
    """

    def __init__(self, session: libtmux.Session, session_name: str, console_win: libtmux.Window, console_pane: libtmux.Pane):
        self.session_existed: bool = False
        self.session_name: str = session_name
        self.session: libtmux.Session = session
        self.console_win: libtmux.Window = console_win
        self.console_pane: libtmux.Pane = console_pane

        self.block_chat: bool = True  # Initially block chat until server is confirmed online.



class DiscordBot(commands.Bot):
    """
    Custom Discord bot class to extend functionality.

    Attributes:
        block_chat (bool): Whether to block chat messages until server is online.
        players_online (int): Number of players currently online on the server.
        tmux (TmuxData): Tmux session and pane data.
        channels (Channels): Channels used by the bot.
    """

    bridge: Bridge

    def __init__(self, tmux_data: TmuxData, **options):
        super().__init__(**options)
        self.block_chat = True  # Initially block chat until server is confirmed online.
        self.tmux = tmux_data
        self.players_online = 0  # Track number of players online.
        self.channels = Channels()
        self.rcon = RconData(self)