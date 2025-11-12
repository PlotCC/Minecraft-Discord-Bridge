from typing import Literal
import discord
from discord.ext import commands
from discord import app_commands
import logging
from random import randint
import re

from traceback import format_exc

import config
from discord_bot import DiscordBot
from rcon import Rcon
import privelege_test

LOG = logging.getLogger("SERVER-COMMANDS")



class ServerCommandsCog(commands.Cog):
    """
    This cog allows the user to control the minecraft server, either by using
    some builtin commands or by running a custom command.

    These use commands that are built into minecraft (or forge) itself.
    """

    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.rcon = bot.rcon
        self.locked_out = False
        self.locked_out_reason = None



    @app_commands.command(name="lockout", description="Lockout the server (clears the whitelist and activates it, and disables the whitelist command).")
    @app_commands.describe(
        reason="The reason for the lockout."
    )
    async def lockout(self, interaction: discord.Interaction, reason: str) -> None:
        """
        Lockout the server.
        """
        if not privelege_test.test(interaction, config.priveleges.owner):
            await interaction.response.send_message(privelege_test.reject_message(config.priveleges.owner))
            return

        try:
            await interaction.response.defer(thinking=True)

            await self.rcon.send_server_command("whitelist on")
            response, id = await self.rcon.send_server_command("whitelist list")

            if response.startswith("There are no whitelisted players"):
                self.locked_out = True
                self.locked_out_reason = reason
                await interaction.followup.send("Server has been locked out.")
                return

            # Regex grab the usernames from the response.
            # "There are 3 whitelisted players: player1, player2, player3"
            # becomes ["player1", "player2", "player3"]
            matches = re.match(r"There are \d+ whitelisted players: (.+)", response)
            if not matches:
                await interaction.followup.send("Failed to parse whitelist response.")
                return
            players = matches.group(1).split(", ")

            for player in players:
                response, id = await self.rcon.send_server_command(f"whitelist remove {player}")
            
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
    async def cancel_lockout(self, interaction: discord.Interaction, disable_whitelist: bool = False) -> None:
        """
        Unlock the server.
        """
        if not privelege_test.test(interaction, config.priveleges.owner):
            await interaction.response.send_message(privelege_test.reject_message(config.priveleges.owner))
            return

        try:
            await interaction.response.defer(thinking=True)
            disabled_whitelist = False

            if disable_whitelist:
                response, id = await self.rcon.send_server_command("whitelist off")
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
        if not privelege_test.test(interaction, config.priveleges.user):
            await interaction.response.send_message(privelege_test.reject_message(config.priveleges.user))
            return

        if self.locked_out:
            await interaction.response.send_message(f"Server is locked out: {self.locked_out_reason}")
            return

        # Some small validation: Ensure the text is alphanumeric or underscore.
        if not username.replace("_", "").isalnum():
            await interaction.response.send_message("Player name must be alphanumeric, but may include underscores.", ephemeral=True)
            return

        try:
            response, id = await self.rcon.send_server_command(f"whitelist add {username}")
            # await interaction.response.send_message(f"Whitelisted player: {player}", delete_after=5.0)
            await interaction.response.send_message(str(response)) # Temporary
        except Exception as e:
            await interaction.response.send_message(f"Failed to whitelist player: {e}")



    @app_commands.command(
        name="list", description="Get a list of players that are currently online."
    )
    async def list(self, interaction: discord.Interaction) -> None:
        if not privelege_test.test(interaction, config.priveleges.user):
            await interaction.response.send_message(privelege_test.reject_message(config.priveleges.user))
            return

        response, id = await self.rcon.send_server_command("list")
        await interaction.response.send_message(response)



    @app_commands.command(name="custom-command", description="Run a custom command.")
    @app_commands.describe(
        command="The command to run."
    )
    async def custom_command(self, interaction: discord.Interaction, command: str) -> None:
        """
        Run a custom command.
        """
        if not privelege_test.test(interaction, config.priveleges.admin):
            await interaction.response.send_message(privelege_test.reject_message(config.priveleges.admin))
            return

        try:
            response, id = await self.rcon.send_server_command(command)
            await interaction.response.send_message(response, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to send command to server: {e}", ephemeral=True)



    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.channel.id == config.rcon.channel_id:
            if message.content.strip() == "":
                return
            if message.content.startswith(config.rcon.command_prefix):
                if not privelege_test.test(message, config.priveleges.rcon_command_privelege):
                    await message.reply(privelege_test.reject_message(config.priveleges.rcon_command_privelege))
                    return

                try:
                    command = message.content[len(config.rcon.command_prefix):].strip()
                    # Run the command.
                    response, id = await self.rcon.send_server_command(command)

                    if response is None or response == "":
                        response = "Command executed successfully. Or not. There was no response."

                    # Send the response as a reply to the message.
                    await message.reply(response)
                except Exception as e:
                    await message.reply(f"Failed to send command to server: {e}")
            elif message.content.startswith(config.rcon.meta_command_prefix):
                if not privelege_test.test(message, config.priveleges.rcon_meta_command_privelege):
                    await message.reply(privelege_test.reject_message(config.priveleges.rcon_meta_command_privelege))
                    return

                command = message.content[len(config.rcon.meta_command_prefix):].strip()

                if command.lower() == "reconnect":
                    try:
                        await self.rcon.instance.close()
                        await self.rcon.instance.connect()
                        await message.reply("Reconnected to RCON server.")
                    except Exception as e:
                        await message.reply(f"Failed to reconnect to RCON server: {e}")
                else:
                    await message.reply(f"Unknown meta-command: {command}")



    @commands.Cog.listener()
    async def on_ready(self):
        pass



    async def cog_load(self):
        LOG.info("Commands cog is loading.")



    async def cog_unload(self):
        LOG.info("Commands cog is unloading.")
        await self.rcon.instance.close() # at worst, the rcon will re-open if something else requires it.



async def setup(bot):
    await bot.add_cog(ServerCommandsCog(bot))
