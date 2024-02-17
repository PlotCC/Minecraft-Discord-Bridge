import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import logging
import asyncio
import os
from minecraftTellrawGenerator import MinecraftTellRawGenerator as tellraw

import config

LOG = logging.getLogger("BACKUP")

async def run_command_subprocess(command: str, timeout: int = 60):
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

async def backup_server(backup_type: str):
    """
    Backup the server.
    """
    LOG.info("Backing up server.")

    file_name = None
    if config.backups["backup_location"] == "":
        file_name = f"backup-{backup_type}-{datetime.datetime.now().strftime('%Y-%m-%d')}-{datetime.datetime.now().strftime('%H-%M-%S')}.zip"
    else:
        file_name = config.backups["backup_name_format"].format(
            type=backup_type,
            date=datetime.datetime.now().strftime('%Y-%m-%d'),
            time=datetime.datetime.now().strftime('%H-%M-%S')
        )

    command = f"zip -r {file_name} {config.backups['world_location']}"

    #stdout, stderr, returncode = await run_command_subprocess(command)
    # Just printing the command for now.
    print(command)
    returncode = 0
    stderr = ""

    # however, we will pretend to wait a bit for the command to finish.
    await asyncio.sleep(5)

    if returncode != 0:
        LOG.error(f"Failed to backup server: {stderr}")

        LOG.warn(f"Removing partial backup: {file_name}")
        # We should be careful that we're not wildly deleting things here.
        os.remove(file_name)
    else:
        LOG.info("Server backup complete.")

    return returncode, stderr


class BackupsCog(commands.Cog):
    """
    This cog controls server backups and restores.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.auto_backup.start()

    
    # Back up the server. Returns true on success, false any time else.
    async def backup_wrapper(self, backup_type: str) -> bool:
        # Step 1: Backup the server.
        LOG.info("Backing up server.")
        try:
            # Notify players on the server a backup is occurring.
            self.bot.send_server_command("tellraw @a " + tellraw.multiple_tellraw(
                tellraw(text="["),
                tellraw(text="Server",color="red"),
                tellraw(text="] "),
                tellraw(text=f"{'Manual' if backup_type == 'manual' else 'Automatic'} server backup starting, the game may lag for a bit!",color="yellow")
            ))

            returncode, stderr = await backup_server(backup_type, timeout=600)

            if returncode != 0:
                LOG.error(f"Failed to backup server (code {returncode}): {stderr}")
                self.bot.bridge_channel.send(
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
                LOG.info("Server backup complete.")

                # Notify players on the server the backup is complete.
                self.bot.send_server_command("tellraw @a " + tellraw.multiple_tellraw(
                    tellraw(text="["),
                    tellraw(text="Server",color="red"),
                    tellraw(text="] "),
                    tellraw(text="Server backup complete!",color="yellow")
                ))
                return True
        except Exception as e:
            LOG.error(f"Failed to backup server: {str(e)}")
            self.bot.bridge_channel.send(
                embed=discord.Embed(
                    color=0xff0000,
                    description=f":x: **Failed to backup server ({backup_type}, exception): {e}**"
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

        return False # This should never be reached, but return false just in case cosmic rays hit the server or something.


    @app_commands.command(name="backup-now", description="Backup the minecraft server right now.")
    @app_commands.checks.cooldown(1, 180.0)
    @app_commands.checks.has_permissions(administrator=True)
    async def backup_now(self, interaction: discord.Interaction) -> None:
        """
        Backup the minecraft server right now.
        """
        await interaction.response.defer(thinking=True)
        
        try:
            returncode, stderr = await backup_server("manual", timeout=600)

            if returncode != 0:
                await interaction.followup.send(f"Failed to backup server (code {returncode}): {stderr}")
            else:
                await interaction.followup.send("Server backup complete.")
        except Exception as e:
            await interaction.followup.send("Failed to backup server: " + str(e))


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

    @commands.Cog.listener()
    async def cog_load(self):
        LOG.info("Backups cog is loading.")
        

    @commands.Cog.listener()
    async def cog_unload(self):
        LOG.warn("Backups cog unloaded!")
        if self.auto_backup.is_running():
            self.auto_backup.stop()
        try:
            await self.bot.bridge_channel.send(":warning: Backups cog unloaded.")
        except Exception as e:
            LOG.error(f"Failed to send cog unload notification: {e}")


async def setup(bot):
    await bot.add_cog(BackupsCog(bot))
