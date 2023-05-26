import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import logging
import asyncio

import config

LOG = logging.getLogger("MC-SERVER")

def stop_server(bot):
    bot.console_pane.send_keys("stop")

def start_server(bot):
    bot.console_pane.reset()
    bot.console_pane.send_keys("cd " + config.server["root"])
    bot.console_pane.send_keys(config.programs["minecraft"])

def get_countdown_message(time:int):
    if time >= 3600 and time % 3600 == 0:
        return f"{time / 3600} hours"
    if time == 1800:
        return "30 minutes"
    if time == 900:
        return "15 minutes"
    if time == 600:
        return "10 minutes"
    if time == 300:
        return "5 minutes"
    if time == 60:
        return "1 minute"
    if time == 30:
        return "30 seconds"
    if time <= 10 and time > 1:
        return f"{time} seconds"
    if time == 1:
        return "1 second"
    if time == 0:
        return "0 seconds"

def get_time_after(time: datetime.time, seconds: int) -> datetime.time:
    hour = time.hour
    minute = time.minute
    second = time.second

    hours_add = seconds // 3600
    seconds %=  3600
    minutes_add = seconds // 60
    seconds %= 60
    seconds_add = seconds

    hour += hours_add
    minute += minutes_add
    second += seconds_add

    hour %= 24
    minute %= 60
    second %= 60

    return datetime.time(hour=hour, minute=minute, second=second, tzinfo=time.tzinfo)

class ServerCog(commands.Cog):
    """
        This cog controls the minecraft server itself.
        Shutdown, startup, etc.

        This also does automatic restarts.
    """
    def __init__(self, bot):
        self.bot = bot
        self.running = False

        # Start the autmatic tasks.
        self.automatic_stop_task.start()

    @app_commands.command(name="shutdown", description="Shut down the Minecraft server.")
    @commands.guild_only()
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.cooldown(1, 180)
    async def shutdown(self, interaction: discord.Interaction) -> None:
        if self.running:
            stop_server(self.bot)
            await interaction.response.send_message("Server is shutting down. Please give it a minute before attempting to start it again.", ephemeral=True)
            self.running = False
        #    self.reset_stop.start()
        #    self.stopping = True
        #elif self.stopping:
        #    await interaction.response.send_message("Server is currently stopping.", ephemeral=True)
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
            self.running = True
        #    self.reset_start.start()
        #    self.starting = True
        #elif self.starting:
        #    await interaction.response.send_message("Server is currently starting up.", ephemeral=True)
        else:
            await interaction.response.send_message("Server is currently running.", ephemeral=True)

    @app_commands.command(name="reboot-schedule", description="Display the automatic restart schedule of the Minecraft server.")
    @commands.guild_only()
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    async def reboot_schedule(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"Server restarts at {config.server['restart_time']} (Timezone: {config.server['restart_time'].tzinfo.key}) daily.", ephemeral=True)
    
    @app_commands.command(name="get-online", description="Get the amount of players currently online.")
    @commands.guild_only()
    async def get_online(self, interaction: discord.Interaction) -> None:
        self.console_pane.send_keys("list")
        await interaction.response.send_message("Ok.", ephemeral=True)

    @tasks.loop(seconds=1)
    async def automatic_restart_task(self):
        if self.running:
            self.restart_time -= 1

            if self.restart_time <= -1:
                self.automatic_restart_task.stop()
                stop_server(self.bot)
                self.running = False
                asyncio.sleep(120)
                if not self.running:
                    LOG.info("Server automatically starting up.")
                    start_server(self.bot)
                    self.running = True
                return

            time = get_countdown_message(self.restart_time)
            if time:
                await self.channel.send(
                    embed=discord.Embed(
                        color=0xff00ff,
                        description=f":warning: Automatic server restart in {time}."
                    )
                )

    @tasks.loop(time=config.server["restart_time"])
    async def automatic_stop_task(self):
        if self.running:
            LOG.info(f"Server automatically shutting down after {config.server['restart_delay']} seconds.")
            self.restart_time = config.server["restart_delay"] + 1
            self.automatic_restart_task.start()

    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = self.bot.get_channel(config.bot["channel_id"])
    
async def setup(bot):
    LOG.info(f"Server shutdown timer is scheduled for {config.server['restart_time']} in timezone {config.server['restart_time'].tzinfo.key}, timer is {config.server['restart_delay']} seconds.")
    LOG.info(f"Server should shut down around {get_time_after(config.server['restart_time'], config.server['restart_delay'])} and start back up around {get_time_after(config.server['restart_time'], config.server['restart_delay'] + 120)}.")
    await bot.add_cog(ServerCog(bot))