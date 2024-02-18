import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import logging
import asyncio
import os
import traceback
from minecraftTellrawGenerator import MinecraftTellRawGenerator as tellraw

import config

LOG = logging.getLogger("BACKUP")

async def run_command_subprocess(command: str, timeout: int = 600):
    """
    Run a command in a subprocess.
    """
    proc = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise
    return stdout.decode(), stderr.decode(), proc.returncode


class BackupsCog(commands.Cog):
    """
    This cog controls server backups and restores.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.auto_backup.start()
        self.backed_up_offline = False

    async def backup_server(self, backup_type: str):
        """
        Backup the server.
        """
        LOG.info("Backing up server.")

        file_name = "backup-{type}-{date}-{time}.zip".format(
            type=backup_type,
            date=datetime.datetime.now().strftime('%Y-%m-%d'),
            time=datetime.datetime.now().strftime('%H-%M-%S')
        )

        file_name = os.path.join(config.backups["backup_location"], file_name)

        command = f"zip -r {file_name} {config.backups['world_location']}"

        LOG.info(f"Command: {command}")

        stdout, stderr, returncode = await run_command_subprocess(command)

        if returncode != 0:
            LOG.warn(f"Failed to backup server: {stderr}")

            LOG.warn(f"Removing partial backup: {file_name}")
            # We should be careful that we're not wildly deleting things here.
            os.remove(file_name)
        else:
            LOG.info("Server backup complete.")

        return returncode, stderr

    
    # Back up the server. Returns true on success, false any time else.
    async def backup_wrapper(self, backup_type: str) -> bool:
        # Step 1: Backup the server.
        try:
            backup_name = "Manual"
            if backup_type == "hourly":
                backup_name = "Hourly"
            else:
                backup_name = "Automatic"


            # Notify players on the server a backup is occurring.
            try:
                self.bot.send_server_command("tellraw @a " + tellraw.multiple_tellraw(
                    tellraw(text="["),
                    tellraw(text="Server",color="red"),
                    tellraw(text="] "),
                    tellraw(text=f"{backup_name} server backup starting, the game may lag for a bit!",color="yellow")
                ))
                self.backed_up_offline = False
            except:
                # If we can't send the message, the server is offline.
                if self.backed_up_offline and backup_type != "manual":
                    LOG.warn("Server is offline, skipping automatic backup.")
                    return False
                self.backed_up_offline = True
            
            # Force the server to save the world.
            try:
                self.bot.send_server_command("save-all")
                
                # Wait for the save to complete.
                await asyncio.sleep(5)
            
                self.bot.send_server_command("save-off")
            except:
                # It is fine if the server is offline, but we should log it.
                LOG.warn("Server must be offline, save-all/save-off failed.")


            returncode, stderr = await self.backup_server(backup_type)

            # Turn the server save back on.
            try:
                self.bot.send_server_command("save-on")
            except Exception as e:
                # It should *mostly* be fine if the server is offline, but we
                # will log this just in case there is some other actual error.
                LOG.warn(f"Failed to turn server save back on: {e}")
                if not self.bot.block_chat:
                    LOG.error("Server chat is not blocked, but failed to send save-on command.")

            if returncode != 0:
                LOG.error(f"Failed to backup server (code {returncode}): {stderr}")
                await self.bot.notification_channel.send(
                    embed=discord.Embed(
                        color=0xff0000,
                        description=f":x: **Failed to backup server ({backup_type}, code {returncode}): {stderr}**"
                    )
                )

                # Notify players on the server the backup failed.
                self.bot.send_server_command("tellraw @a " + tellraw.multiple_tellraw(
                    tellraw(text="["),
                    tellraw(text="Server",color="red"),
                    tellraw(text="] "),
                    tellraw(text="Server backup failed!",color="red")
                ))
                return False
            else:
                # Notify players on the server the backup is complete.
                self.bot.send_server_command("tellraw @a " + tellraw.multiple_tellraw(
                    tellraw(text="["),
                    tellraw(text="Server",color="green"),
                    tellraw(text="] "),
                    tellraw(text="Server backup complete!",color="yellow")
                ))
                return True
        except Exception as e:
            LOG.error(f"Failed to backup server, threw exception: {type(e).__name__}, args: {e.args}, str: {e}")
            try:
                self.bot.notifications
                await self.bot.notification_channel.send(
                    embed=discord.Embed(
                        color=0xff0000,
                        description=f":x: **Failed to backup server ({backup_type}, exception): {e}**"
                    )
                )
            except:
                None

            try:
                # Notify players on the server the backup failed.
                self.bot.send_server_command("tellraw @a " + tellraw.multiple_tellraw(
                    tellraw(text="["),
                    tellraw(text="Server",color="red"),
                    tellraw(text="] "),
                    tellraw(text="Server backup failed!",color="red")
                ))
            except:
                None

            return False

        return False # This should never be reached, but return false just in case cosmic rays hit the server or something.

    # @app_commands.checks.cooldown(1, 180.0)

    @app_commands.command(name="backup-now", description="Backup the minecraft server right now.")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup_now(self, interaction: discord.Interaction) -> None:
        """
        Backup the minecraft server right now.
        """
        await interaction.response.defer(thinking=True)
        
        try:
            LOG.info("Manual backup starting...")
            ok = await self.backup_wrapper("manual")

            if ok:
                await interaction.followup.send("Server backup complete.")
            else:
                await interaction.followup.send(f"Failed to backup server, check logs for details.")
        except Exception as e:
            await interaction.followup.send("Failed to backup server: " + str(e))

            # Log stacktrace to console
            LOG.error(traceback.format_exc())

    @app_commands.command(name="restore", description="Restore a backup by its ID.")
    @app_commands.describe(
        id="The ID of the backup to restore."
    )
    @app_commands.checks.cooldown(1, 180.0)
    @app_commands.checks.has_permissions(administrator=True)
    async def restore(self, interaction: discord.Interaction, id: str) -> None:
        """
        Restore a backup.
        """
        await interaction.response.send_message("This command is not yet implemented.", ephemeral=True)
        # await interaction.response.defer(thinking=True)
    

    @app_commands.command(name="list-backups", description="List all backups.")
    @app_commands.checks.cooldown(1, 180.0)
    @app_commands.checks.has_permissions(administrator=True)
    async def list_backups(self, interaction: discord.Interaction) -> None:
        """
        List all backups.
        """
        await interaction.response.send_message("This command is not yet implemented.", ephemeral=True)
        # await interaction.response.defer(thinking=True)


    @app_commands.command(name="stop-backups", description="Stop automatic backups.")
    @app_commands.checks.cooldown(1, 180.0)
    @app_commands.checks.has_permissions(administrator=True)
    async def stop_backups(self, interaction: discord.Interaction) -> None:
        """
        Stop automatic backups.
        """
        if not self.auto_backup.is_running():
            await interaction.response.send_message("Automatic backups are not running.", ephemeral=True)
            return
        self.auto_backup.stop()
        await interaction.response.send_message("Automatic backups stopped.", ephemeral=True)


    @app_commands.command(name="start-backups", description="Start automatic backups.")
    @app_commands.checks.cooldown(1, 180.0)
    @app_commands.checks.has_permissions(administrator=True)
    async def start_backups(self, interaction: discord.Interaction) -> None:
        """
        Start automatic backups.
        """
        if self.auto_backup.is_running():
            await interaction.response.send_message("Automatic backups are already running.", ephemeral=True)
            return
        self.auto_backup.start()
        await interaction.response.send_message("Automatic backups started.", ephemeral=True)


    async def cleanup_backups(self):
        if True: # TODO: Finish the cleanup function.
            LOG.info("Cleanup called, but not yet implemented.")
            return
        # Step 1: Clean up the backup directory, keeping only the specified number of hourly, daily, and weekly backups.
        LOG.info("Cleaning up backup directory.")
        
        # 1.a) Get a list of all backups.
        backups = []
        for file in os.listdir(config.backups["backup_location"]):
            if file.endswith(".zip"):
                backups.append(file)
        
        # 1.b) Sort the backups by date.

    
    @tasks.loop(hours=1)
    async def auto_backup(self):
        """
        Automatically backup the server.
        """
        if (await self.backup_wrapper("hourly")):
            await self.cleanup_backups()
        

    @commands.Cog.listener()
    async def on_ready(self):
        None

    async def cog_load(self):
        LOG.info("Backups cog is loading.")
        

    async def cog_unload(self):
        LOG.warn("Backups cog unloaded!")
        if self.auto_backup.is_running():
            self.auto_backup.stop()
        try:
            await self.bot.notification_channel.send(":warning: Backups cog unloaded.")
        except Exception as e:
            LOG.error(f"Failed to send cog unload notification: {e}")


async def setup(bot):
    await bot.add_cog(BackupsCog(bot))
