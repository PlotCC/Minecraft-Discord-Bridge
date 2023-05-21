from discord.ext import commands, tasks
from discord import app_commands
import time
from minecraftTellrawGenerator import MinecraftTellRawGenerator as tellraw

import config

class ServerCog(commands.Cog):
    """
        This cog controls the minecraft server itself.
        Shutdown, startup, etc.

        This also does automatic restarts.
    """
    def __init__(self, bot):
        self.bot = bot
        self.running = False

    group = app_commands.Group(name="minecraft", description="Minecraft server controls.")

    @group.command(name="shutdown", description="Shut down the Minecraft server.")
    @commands.guild_only()
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.cooldown(1, 180)
    async def shutdown(self, ctx):
        if self.running:
            self.bot.console_pane.send_keys("stop")
            ctx.send("Server is shutting down. Please give it a minute before attempting to start it again.", ephemeral=True)
            await time.sleep(60)
            self.running = False
        else:
            ctx.send("Server is not currently running.", ephemeral=True)

    @group.command(name="startup", description="Start up the Minecraft server.")
    @commands.guild_only()
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.cooldown(1, 180)
    async def startup(self, ctx):
        if not self.running:
            self.bot.console_pane.send_keys(config.programs["minecraft"])
            self.running = True
        else:
            ctx.send("Server is currently running.", ephemeral=True)

    @group.command(name="reboot-schedule", description="Display the automatic restart schedule of the Minecraft server.")
    @commands.guild_only()
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    async def reboot_schedule(self, ctx):
        ctx.send(f"Server restarts at {config.server['restart_time']} UTC daily.", ephemeral=True)
    

    @tasks.loop(time=config.server["restart_time"])
    async def automatic_restart_task(self):
        await self.shutdown()
        await time.sleep(60)
        await self.startup()
    
    async def setup(bot):
        await bot.add_cog(ServerCog(bot))