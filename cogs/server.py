import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import logging

import config

LOG = logging.getLogger("MC-SERVER")

def stop_server(bot):
    bot.console_pane.send_keys("stop")

def start_server(bot):
    bot.console_pane.send_keys(config.programs["minecraft"])

class ServerCog(commands.Cog):
    """
        This cog controls the minecraft server itself.
        Shutdown, startup, etc.

        This also does automatic restarts.
    """
    def __init__(self, bot):
        self.bot = bot
        self.running = False
        self.starting = False
        self.stopping = False

        # Start the autmatic tasks.
        self.automatic_stop_task.start()
        self.automatic_start_task.start() # And boot the server when the bot starts

    @app_commands.command(name="shutdown", description="Shut down the Minecraft server.")
    @commands.guild_only()
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.cooldown(1, 180)
    async def shutdown(self, interaction: discord.Interaction) -> None:
        if self.running:
            stop_server(self.bot)
            await interaction.response.send_message("Server is shutting down. Please give it a minute before attempting to start it again.", ephemeral=True)
            self.reset_stop.start()
            self.stopping = True
        elif self.stopping:
            await interaction.response.send_message("Server is currently stopping.", ephemeral=True)
        else:
            await interaction.response.send_message("Server is not currently running.", ephemeral=True)

    @app_commands.command(name="startup", description="Start up the Minecraft server.")
    @commands.guild_only()
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.cooldown(1, 180)
    async def startup(self, interaction: discord.Interaction) -> None:
        if not self.running:
            start_server(self.bot)
            await interaction.response.send_message("Server is starting up.", ephemeral=True)
            self.reset_start.start()
            self.starting = True
        elif self.starting:
            await interaction.response.send_message("Server is currently starting up.", ephemeral=True)
        else:
            await interaction.response.send_message("Server is currently running.", ephemeral=True)

    @app_commands.command(name="reboot-schedule", description="Display the automatic restart schedule of the Minecraft server.")
    @commands.guild_only()
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    async def reboot_schedule(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"Server restarts at {config.server['restart_time']} UTC daily.", ephemeral=True)

    # TODO Notify players of automatic restart.

    @tasks.loop(minutes=1)
    async def reset_stop(self):
        LOG.info("Reset stop called")
        self.reset_stop.stop()
        self.running = False
        self.stopping = False
        self.console_pane.reset()

    @tasks.loop(minutes=1)
    async def reset_start(self):
        LOG.info("Reset start called")
        self.reset_start.stop()
        self.running = True
        self.starting = False

    @tasks.loop(time=config.server["restart_time"])
    async def automatic_stop_task(self):
        LOG.info("Server automatically shutting down.")
        stop_server(self.bot)
        self.starting = True
        self.automatic_start_task.start()
        self.reset_stop.start()

    @tasks.loop(minutes=2)
    async def automatic_start_task(self):
        LOG.info("Server automatically starting up.")
        start_server(self.bot)
        self.stopping = True
        self.automatic_start_task.stop()
        self.reset_start.start()

async def setup(bot):
    await bot.add_cog(ServerCog(bot))