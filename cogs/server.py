import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import logging
import asyncio

from rcon import Rcon
import config
from utilities.parse_tmux_pid import get_tmux_pid

LOG = logging.getLogger("MC-SERVER")

# Stop the server.
async def stop_server(bot):
    await bot.send_server_command("stop")

# Start the server.
def start_server(bot):
    bot.console_pane.reset()
    bot.send_console_command("cd " + config.server["root"])
    bot.send_console_command(config.programs["minecraft"])


def get_server_process():
    # Get the tmux session.
    tree = get_tmux_pid(config.tmux_data["tmux_session"])

    # Check if java process exists with the -jar argument.
    # NOTE: If we change the amount of tmux windows in the future, we will likely need to change this.

    # Get the java process.
    def descend(node):
        for child in node["children"]:
            if child["process_name"].find("java"):
                return child
            else:
                return descend(child)

    return descend(tree)


def get_countdown_message(time: int):
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
    if time == 0:
        return "now"


def get_time_after(time: datetime.time, seconds: int) -> datetime.time:
    hour = time.hour
    minute = time.minute
    second = time.second

    hours_add = seconds // 3600
    seconds %= 3600
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

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_message = None
        self.server_pid = None
        self.running = False
        self.stopping = False
        self.cancel_restart = False
        self.restart_lock = False
        self.crash_lock = False
        self.notifications = False
        self.skip_restart = 0
        self.restart_time = 0
        self.crash_count = 0
        self.rcon = Rcon()

        # Start the autmatic tasks.
        self.automatic_stop_task.start()
        self.check_server_running.start()

        # Function to send a command to the server console, to be used by cogs rather than invoking the console directly.
        async def send_server_command(command: str):
            """
            Send a command to the console. This fails if the server is offline.
            """
            if not self.running:
                raise Exception("Server is offline, cannot send command to server console.")
            
            # bot.console_pane.send_keys(command)
            await self.rcon.send(command)
        bot.send_server_command = send_server_command

        # Function to send a command to the console, to be used by cogs rather than invoking the console directly.
        def send_console_command(command: str):
            """
            Send a command to the console. This fails if the server is online.
            """
            if self.running:
                raise Exception("Server is online, cannot send command to console.")
            
            bot.console_pane.send_keys(command)
        bot.send_console_command = send_console_command

    @app_commands.command(
        name="shutdown", description="Shut down the Minecraft server."
    )
    @app_commands.checks.cooldown(1, 180.0)
    @app_commands.checks.has_permissions(administrator=True)
    async def shutdown(self, interaction: discord.Interaction) -> None:
        if self.running:
            await stop_server(self.bot)
            self.stopping = True
            await interaction.response.send_message(
                "Server is shutting down. Please give it a minute before attempting to start it again."
            )
        else:
            await interaction.response.send_message(
                "Server is not currently running.", ephemeral=True
            )
            await asyncio.sleep(4)
            await interaction.delete_original_response()

    @app_commands.command(name="startup", description="Start up the Minecraft server.")
    @app_commands.checks.cooldown(1, 180.0)
    @app_commands.checks.has_permissions(administrator=True)
    async def startup(self, interaction: discord.Interaction) -> None:
        if not self.running:
            if self.crash_lock:
                await interaction.response.send_message(
                    "Server startup is currently locked due to a crash-loop.",
                    ephemeral=True,
                )
                return

            start_server(self.bot)
            await interaction.response.send_message("Server startup has been queued.")
            self.running = True
            self.restart_lock = False
        else:
            await interaction.response.send_message(
                "Server is currently running.", ephemeral=True
            )
            await asyncio.sleep(4)
            await interaction.delete_original_response()

    @app_commands.command(
        name="cancel-restart", description="Cancel the current restart timer."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def cancel_restart_cmd(self, interaction: discord.Interaction) -> None:
        if self.restart_time == 0:
            await interaction.response.send_message(
                "No server restart in progress.", ephemeral=True
            )
            await asyncio.sleep(4)
            await interaction.delete_original_response()
            return

        self.cancel_restart = True
        await interaction.response.send_message("Server restart will be cancelled.")

    @app_commands.command(
        name="skip-restart",
        description="Skip the next <n> server restarts. Defaults to 1.",
    )
    @app_commands.describe(
        count="The amount of restarts to skip, defaults to a single restart."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def skip_restart_cmd(
        self, interaction: discord.Interaction, count: int = 1
    ) -> None:
        self.skip_restart = count
        await interaction.response.send_message(
            f"The next {count} restarts will be skipped."
        )

    @app_commands.command(
        name="queue-restart",
        description="Queue a restart in <seconds> time. Defaults to one hour time (3600 seconds).",
    )
    @app_commands.describe(
        time="The amount of time to delay the restart by. This will override the current restart timer, if one is running."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def queue_restart(
        self, interaction: discord.Interaction, time: int = 3601
    ) -> None:
        self.restart_time = time + 1
        if not self.automatic_restart_task.is_running():
            self.restart_lock = True
            self.automatic_restart_task.start()
            await interaction.response.send_message(
                f"Restart queued for {time} seconds."
            )
        else:
            await interaction.response.send_message(
                f"Restart delay updated to {time} seconds."
            )

    @app_commands.command(
        name="set-state",
        description="Mark the server as online or offline, useful if server module is reloaded.",
    )
    @app_commands.describe(online="The server state.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_state(self, interaction: discord.Interaction, online: bool) -> None:
        self.running = online
        await interaction.response.send_message(
            f"Set server online state to {online}.", delete_after=4
        )
        if self.session_message != None:
            await asyncio.sleep(4)
            await self.session_message.delete()
            self.session_message = None

    @app_commands.command(
        name="unlock",
        description="Unlock the server startup after being stuck in a crash loop.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def unlock(self, interaction: discord.Interaction) -> None:
        self.crash_lock = False
        self.crash_count = 0
        await interaction.response.send_message(
            "Server startup unlocked.", ephemeral=True, delete_after=4
        )

    @app_commands.command(
        name="reboot-schedule",
        description="Display the automatic restart schedule of the Minecraft server.",
    )
    async def reboot_schedule(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            f"Server restart begins at {config.server['restart_time']} (Timezone: {config.server['restart_time'].tzinfo.key}), delay is {config.server['restart_delay']} seconds.",
            ephemeral=True,
        )

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
                await stop_server(self.bot)
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
                await self.bot.bridge_channel.send(
                    embed=discord.Embed(
                        color=0xFF00FF,
                        description=f":warning: Automatic server restart in {time}.",
                    )
                )

    @tasks.loop(time=config.server["restart_time"])
    async def automatic_stop_task(self):
        if self.restart_lock:
            return

        if self.running:
            self.restart_lock = True
            LOG.info(
                f"Server automatically shutting down after {config.server['restart_delay']} seconds."
            )
            self.restart_time = config.server["restart_delay"] + 1
            if not self.automatic_restart_task.is_running():
                self.automatic_restart_task.start()

    @tasks.loop(count=1)
    async def check_crash_loop(self):
        await asyncio.sleep(300)
        LOG.info("Crash loop timeout.")
        self.check_crash_loop.stop()

    # Check that the server is still running. If the server shuts down unexpectedly, this will detect it.
    @tasks.loop(seconds=5)
    async def check_server_running(self):
        if not self.running:
            self.bot.block_chat = True
            return

        server_process = get_server_process()

        if server_process:
            self.bot.block_chat = False
        else:
            self.bot.block_chat = True
            # Server stopped!
            LOG.warn("Server stopped!")
            if self.stopping:
                self.running = False
                self.stopping = False
                self.crash_count = 0
                return  # Nothing to worry about!

            self.running = False
            self.restart_lock = False

            # Check if the crash loop task is running
            if self.check_crash_loop.is_running():
                # If it is, that means we crashed within 5 minutes of crashing. Increment crash count.
                self.crash_count += 1
            else:
                # If it isn't, it means we are outside the crash count. Reset the counter.
                self.crash_count = 1

            self.check_crash_loop.stop()
            self.check_crash_loop.cancel()
            await asyncio.sleep(1)  # Hopefully this is enough for the task to stop?
            self.check_crash_loop.start()

            if self.crash_count >= 5:
                LOG.error("Server crashed 5 times in a row, not restarting.")
                self.restart_lock = True
                self.crash_lock = True

                content = None
                embed = discord.Embed(
                    color=0xFF0000,
                    description=":no_entry: Crash loop detected, server startup locked.",
                )
                if self.notifications:
                    if config.server["ping_role_in_bridge"]:
                        content = self.notification_ping
                    else:
                        await self.bot.notification_channel.send(
                            self.notification_ping
                            + " The server has crashed 5 times in a row and has been locked. Please investigate."
                        )
                        embed.set_footer(text="Operators have been notified.")

                await self.bot.bridge_channel.send(content=content, embed=embed)
            else:
                LOG.warn(
                    f"Server crashed ({self.crash_count} times in a row), restarting."
                )
                start_server(self.bot)
                self.running = True
                self.restart_lock = False

                content = None
                embed = discord.Embed(
                    color=0xFFFF00 if self.crash_count < 4 else 0xFFAA00,
                    description=":warning: Server crash detected, restarting."
                    if self.crash_count < 4
                    else ":warning: Server crash detected, restarting. Server is potentially in a crash-loop.",
                )
                if self.notifications:
                    if config.server["ping_role_in_bridge"]:
                        content = self.notification_ping
                    else:
                        await self.bot.notification_channel.send(
                            self.notification_ping
                            + " The server has crashed and is restarting."
                        )
                        embed.set_footer(text="Operators have been notified.")

                await self.bot.bridge_channel.send(content=content, embed=embed)

    async def get_channels(self):
        LOG.info("Getting channels.")

        LOG.info("  Bridge channel.")
        self.bot.bridge_channel = self.bot.get_channel(config.bot["channel_id"])
        LOG.info("    Got bridge channel.")

        LOG.info("  Notification channel (if enabled)")
        self.notifications = config.server["enable_notifications"]
        if self.notifications:
            self.notification_ping = (
                "<@" + str(config.server["notification_role_id"]) + ">"
            )

            if config.server["ping_role_in_bridge"]:
                LOG.info(
                    "    Not getting notification channel, ping_role_in_bridge is true. Ping will be appended to the message in the bridge channel."
                )
            else:
                self.bot.notification_channel = self.bot.get_channel(
                    config.server["notification_channel_id"]
                )
                LOG.info("    Got notification channel.")
        else:
            LOG.info(
                "    Not getting notification channel, notifications are disabled."
            )

        # TODO: Confirm that the channels were actually "gotten" in the above code.

        if self.bot.session_existed:
            # Check if java process exists with the -jar argument.
            # NOTE: If we change the amount of tmux windows in the future, we will likely need to change this.

            # Get the java process.
            java_process = get_server_process()

            base_embed = None

            if not java_process:
                base_embed = discord.Embed(
                    color=0xFF00FF,
                    description="Session already exists and no java process was found. Assuming the server is offline.",
                )
                self.running = False
                self.restart_lock = False
            else:
                base_embed = discord.Embed(
                    color=0xFF00FF,
                    description="Session already exists and a java process was found. Assuming the server is online.",
                )
                self.running = True
                self.restart_lock = False
                self.server_pid = java_process["pid"]

            base_embed.set_footer(text="Use /set-state to override this.")

            self.session_message = await self.bot.bridge_channel.send(embed=base_embed)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.get_channels()

    async def cog_load(self):  # If the cog reloads, this can get the channel again.
        if self.bot.is_ready():
            await self.get_channels()

    async def cog_unload(self):
        if self.automatic_restart_task.is_running():
            self.automatic_restart_task.stop()
        if self.automatic_stop_task.is_running():
            self.automatic_stop_task.stop()
        if self.check_server_running.is_running():
            self.check_server_running.cancel()  # This one doesn't need to safely exit.
        if self.check_crash_loop.is_running():
            self.check_crash_loop.cancel() # This one doesn't need to safely exit.

        try:
            await self.bot.notification_channel.send(":warning: Server cog unloaded.")
        except Exception as e:
            LOG.error(f"Failed to send cog unload notification: {e}")


async def setup(bot):
    LOG.info(
        f"Server shutdown timer is scheduled for {config.server['restart_time']} in timezone {config.server['restart_time'].tzinfo.key}, timer is {config.server['restart_delay']} seconds."
    )
    LOG.info(
        f"Server should shut down around {get_time_after(config.server['restart_time'], config.server['restart_delay'])} and start back up around {get_time_after(config.server['restart_time'], config.server['restart_delay'] + 120)}."
    )
    await bot.add_cog(ServerCog(bot))
