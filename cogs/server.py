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
    if time > 3600 and time % 3600 == 0:
        return f"{time // 3600} hours"
    if time == 3600:
        return "1 hour"
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
        self.session_message = None
        self.running = False
        self.cancel_restart = False
        self.restart_lock = False
        self.skip_restart = 0
        self.restart_time = 0

        # Start the autmatic tasks.
        self.automatic_stop_task.start()

    @app_commands.command(name="shutdown", description="Shut down the Minecraft server.")
    @app_commands.checks.cooldown(1, 180.0)
    @app_commands.checks.has_permissions(administrator=True)
    async def shutdown(self, interaction: discord.Interaction) -> None:
        if self.running:
            stop_server(self.bot)
            await interaction.response.send_message("Server is shutting down. Please give it a minute before attempting to start it again.")
            self.running = False
        else:
            await interaction.response.send_message("Server is not currently running.", ephemeral=True)
            await asyncio.sleep(4)
            await interaction.delete_original_response()

    @app_commands.command(name="startup", description="Start up the Minecraft server.")
    @app_commands.checks.cooldown(1, 180.0)
    @app_commands.checks.has_permissions(administrator=True)
    async def startup(self, interaction: discord.Interaction) -> None:
        if not self.running:
            start_server(self.bot)
            await interaction.response.send_message("Server is starting up.")
            self.running = True
            self.restart_lock = False
        else:
            await interaction.response.send_message("Server is currently running.", ephemeral=True)
            await asyncio.sleep(4)
            await interaction.delete_original_response()
    
    @app_commands.command(name="cancel-restart", description="Cancel the current restart timer.")
    @app_commands.checks.has_permissions(administrator=True)
    async def cancel_restart_cmd(self, interaction: discord.Interaction) -> None:
        if self.restart_time == 0:
            await interaction.response.send_message("No server restart in progress.", ephemeral=True)
            await asyncio.sleep(4)
            await interaction.delete_original_response()
            return
        
        self.cancel_restart = True
        await interaction.response.send_message("Server restart will be cancelled.")

    @app_commands.command(name="skip-restart", description="Cancel the current restart timer.")
    @app_commands.describe(count="The amount of restarts to skip, defaults to a single restart.")
    @app_commands.checks.has_permissions(administrator=True)
    async def skip_restart_cmd(self, interaction: discord.Interaction, count: int = 1) -> None:
        self.skip_restart = count
        await interaction.response.send_message(f"The next {count} restarts will be skipped.")

    @app_commands.command(name="queue-restart", description="Queue a restart in <seconds> time. Defaults to one hour time (3600 seconds).")
    @app_commands.describe(time="The amount of time to delay the restart by. This will override the current restart timer, if one is running.")
    @app_commands.checks.has_permissions(administrator=True)
    async def queue_restart(self, interaction: discord.Interaction, time: int = 3601) -> None:
        self.restart_time = time + 1
        if not self.automatic_restart_task.is_running():
            self.restart_lock = True
            self.automatic_restart_task.start()
            await interaction.response.send_message(f"Restart queued for {time} seconds.")
        else:
            await interaction.response.send_message(f"Restart delay updated to {time} seconds.")
    
    @app_commands.command(name="set-state", description="Mark the server as online or offline, useful if server module is reloaded.")
    @app_commands.describe(online="The server state.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_state(self, interaction: discord.Interaction, online: bool = True) -> None:
        self.running = online
        await interaction.response.send_message(f"Set server online state to {online}.", delete_after=4)
        if self.session_message != None:
            await asyncio.sleep(4)
            await self.session_message.delete()
            self.session_message = None

    @app_commands.command(name="reboot-schedule", description="Display the automatic restart schedule of the Minecraft server.")
    async def reboot_schedule(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"Server restart begins at {config.server['restart_time']} (Timezone: {config.server['restart_time'].tzinfo.key}), delay is {config.server['restart_delay']} seconds.", ephemeral=True)
    
    @app_commands.command(name="list-players", description="Get the amount of players currently online.")
    async def get_online(self, interaction: discord.Interaction) -> None:
        if self.running:
            self.bot.console_pane.send_keys("list")
            await interaction.response.send_message("Fetching player list...", delete_after=2)
        else:
            await interaction.response.send_message("Server is offline!", ephemeral=True, delete_after=4)

    @tasks.loop(seconds=1)
    async def automatic_restart_task(self):
        if self.cancel_restart:
            self.cancel_restart = False
            self.restart_lock = False
            self.automatic_restart_task.stop()
            return

        if self.skip_restart > 0:
            self.skip_restart -= 1
            self.restart_lock = False
            self.automatic_restart_task.stop()
            return
        
        if self.running:
            self.restart_time -= 1

            if self.restart_time <= -1:
                self.automatic_restart_task.stop()
                stop_server(self.bot)
                self.running = False
                await asyncio.sleep(120)
                if not self.running:
                    LOG.info("Server automatically starting up.")
                    start_server(self.bot)
                    self.running = True
                
                self.restart_lock = False
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
        if self.restart_lock:
            return
        
        if self.running:
            self.restart_lock = True
            LOG.info(f"Server automatically shutting down after {config.server['restart_delay']} seconds.")
            self.restart_time = config.server["restart_delay"] + 1
            if not self.automatic_restart_task.is_running():
                self.automatic_restart_task.start()

    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = self.bot.get_channel(config.bot["channel_id"])
        if self.bot.session_existed:
            self.session_message = await self.channel.send(
                embed=discord.Embed(
                    color=0xff00ff,
                    description=f":warning: Session already exists and I was unable to determine if the server was online. Please use /set-state to configure."
                )
            )
            
    
    def cog_unload(self):
        if self.automatic_restart_task.is_running():
            self.automatic_restart_task.stop()
        if self.automatic_stop_task.is_running():
            self.automatic_stop_task.stop()
    
async def setup(bot):
    LOG.info(f"Server shutdown timer is scheduled for {config.server['restart_time']} in timezone {config.server['restart_time'].tzinfo.key}, timer is {config.server['restart_delay']} seconds.")
    LOG.info(f"Server should shut down around {get_time_after(config.server['restart_time'], config.server['restart_delay'])} and start back up around {get_time_after(config.server['restart_time'], config.server['restart_delay'] + 120)}.")
    await bot.add_cog(ServerCog(bot))