import discord
from discord.ext import commands
from discord import app_commands
import logging
from random import randint
import re

from traceback import format_exc

import config
from rcon import Rcon

LOG = logging.getLogger("SERVER-COMMANDS")


def is_owner(interaction: discord.Interaction) -> bool:
    return interaction.user.id == config.bot["owner_id"]


funny_denial_messages = [
    "# NUH UH", # Lazy man's way of adding a higher chance of this message: just add it multiple times.
    "# NUH UH",
    "# NUH UH",
    "# NUH UH",
    "# NUH UH",
    "# NUH UH",
    "# NUH UH",
    "+1 for trying, but no.",
    "+1 for trying, but no.",
    "+1 for trying, but no.",
    "+1 for trying, but no.",
    "+1 for trying, but no.",
    "+1 for trying, but no.",
    "+1 for trying, but no.",
    "+1 for trying, but no.",
    "+1 for trying, but no.",
    "+1 for trying, but no.",
    "+1 for trying, but no.",
    "I'm sorry, Dave. I'm afraid I can't do that.",
    "I'm sorry, Dave. I'm afraid I can't do that.",
    "I'm sorry, Dave. I'm afraid I can't do that.",
    "The system has decided you are not worthy of holding this power.",
    "The system has decided you are not worthy of holding this power.",
    "The system has decided you are not worthy of holding this power.",
    "You're not the owner of this bot.",
    "You're not my dad!",
    "This is a VIP-only area. Get out.",
    "Try again in another universe.",
    "You're not on the guest list.",
    "Try asking nicely next time?",
    "Your credentials are expired.",
    "Someone told me you weren't allowed to do that, and I always listen to strangers.",
    "Meh, I don't feel like it.",
    "I'm in your walls.",
    "SHUT UP SHUT UP SHUT UP",
    "lalalalalala I can't hear you",
    "Sorry, we don't just let *anyone* run commands here.",
]

def get_denial_message():
    return funny_denial_messages[randint(0, len(funny_denial_messages)-1)]


class ServerCommandsCog(commands.Cog):
    """
    This cog allows the user to control the minecraft server, either by using
    some builtin commands or by running a custom command.

    These use commands that are built into minecraft (or forge) itself.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.rcon = Rcon()
        self.locked_out = False
        self.locked_out_reason = None

    

    @app_commands.command(name="lockout", description="Lockout the server (clears the whitelist and activates it, and disables the whitelist command).")
    @app_commands.describe(
        reason="The reason for the lockout."
    )
    @app_commands.check(is_owner)
    async def lockout(self, interaction: discord.Interaction, reason: str) -> None:
        """
        Lockout the server.
        """
        try:
            await interaction.response.defer(thinking=True)

            await self.rcon.send("whitelist on")
            response, id = await self.rcon.send("whitelist list")

            if response.startswith("There are no whitelisted players"):
                self.locked_out = True
                self.locked_out_reason = reason
                await interaction.followup.send("Server has been locked out.")
                return

            # Regex grab the usernames from the response.
            # "There are 3 whitelisted players: player1, player2, player3"
            # becomes ["player1", "player2", "player3"]
            players = re.match(r"There are \d+ whitelisted players: (.+)", response).group(1).split(", ")

            for player in players:
                response, id = await self.rcon.send(f"whitelist remove {player}")
            
            await interaction.followup.send("Server has been locked out.")
            self.locked_out = True
            self.locked_out_reason = reason

        except Exception as e:
            if interaction.response.is_done():
                await interaction.followup.send(content=f"Failed to lockout the server: {e}")
            else:
                await interaction.response.send_message(f"Failed to lockout the server: {e}", ephemeral=True)



    @app_commands.command(name="cancel_lockout", description="Unlock the server (Re-enable the whitelist command, and optionally disable the whitelist).")
    @app_commands.describe(
        disable_whitelist="Disable the whitelist after unlocking."
    )
    @app_commands.check(is_owner)
    async def cancel_lockout(self, interaction: discord.Interaction, disable_whitelist: bool = False) -> None:
        """
        Unlock the server.
        """
        try:
            await interaction.response.defer(thinking=True)
            disabled_whitelist = False

            if disable_whitelist:
                response, id = await self.rcon.send("whitelist off")
                if response.endswith("turned off"):
                    disabled_whitelist = True
            
            self.locked_out = False
            self.locked_out_reason = None

            if disabled_whitelist:
                await interaction.followup.send(content="Server unlocked, whitelist disabled.")
            else:
                await interaction.followup.send(content="Server unlocked.")

        except Exception as e:
            if interaction.response.is_done():
                await interaction.followup.send(content=f"Failed to unlock the server: {e}")
            else:
                await interaction.response.send_message(f"Failed to unlock the server: {e}", ephemeral=True)
                    



    @app_commands.command(name="whitelist", description="Add a player to the whitelist.")
    @app_commands.describe(
        username="The username of the player to whitelist."
    )
    async def whitelist(self, interaction: discord.Interaction, username: str) -> None:
        """
        Add a player to the whitelist.
        """

        if self.locked_out:
            await interaction.response.send_message(f"Server is locked out: {self.locked_out_reason}")
            return

        # Some small validation: Ensure the text is alphanumeric or underscore.
        if not username.replace("_", "").isalnum():
            await interaction.response.send_message("Player name must be alphanumeric, but may include underscores.", ephemeral=True)
            return

        try:
            response, id = await self.rcon.send(f"whitelist add {username}")
            # await interaction.response.send_message(f"Whitelisted player: {player}", delete_after=5.0)
            await interaction.response.send_message(str(response)) # Temporary
        except Exception as e:
            await interaction.response.send_message(f"Failed to whitelist player: {e}")



    @app_commands.command(
        name="list", description="Get a list of players that are currently online."
    )
    async def list(self, interaction: discord.Interaction) -> None:
        response, id = await self.rcon.send("list")
        await interaction.response.send_message(response)
    


    @app_commands.command(name="custom-command", description="Run a custom command.")
    @app_commands.describe(
        command="The command to run."
    )
    @app_commands.check(is_owner)
    async def custom_command(self, interaction: discord.Interaction, command: str) -> None:
        """
        Run a custom command.
        """
        try:
            response, id = await self.rcon.send(command)
            await interaction.response.send_message(response, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to send command to server: {e}", ephemeral=True)
    

    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.channel.id == config.server["rcon_channel_id"]:
            if message.author.id != config.bot["owner_id"]:
                LOG.info(f"Message from {message.author} is not the owner.")
                await message.reply(get_denial_message())
                return

            try:
                # Run the command.
                response, id = await self.rcon.send(message.content)

                if response is None or response == "":
                    response = "Command executed successfully. Or not. There was no response."

                # Send the response as a reply to the message.
                await message.reply(response)
            except Exception as e:
                await message.reply(f"Failed to send command to server: {e}")




    @commands.Cog.listener()
    async def on_ready(self):
        None



    async def cog_load(self):
        LOG.info("Commands cog is loading.")
        


    async def cog_unload(self):
        LOG.info("Commands cog is unloading.")
        self.rcon.close() # at worst, the rcon will re-open if something else requires it.


async def setup(bot):
    await bot.add_cog(ServerCommandsCog(bot))
