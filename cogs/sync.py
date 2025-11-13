import discord
from discord.ext import commands
from discord import app_commands
import logging

import config
from discord_bot import DiscordBot
import privilege_test

LOG = logging.getLogger("SYNC")



class SyncCog(commands.Cog):
    def __init__(self, bot: DiscordBot):
        self.bot = bot



    @app_commands.command(name="resync", description="Properly re-synchronize the command tree, deleting old commands as well.")
    async def resync(self, interaction: discord.Interaction) -> None:
        """
        Properly re-synchronize the command tree, deleting old commands as well.
        """

        if not privilege_test.test(interaction, config.privileges.owner):
            await interaction.response.send_message(privilege_test.reject_message(config.privileges.owner))
            return

        LOG.info("Resyncing command tree...")

        # Delete all commands.
        for command in self.bot.walk_commands():
            try: await command.delete() # type: ignore dont care didnt ask
            except: pass
        
        # Re-register all commands.
        await self.bot.tree.sync()

        await interaction.response.send_message("Resynced command tree.")



async def setup(bot):
    await bot.add_cog(SyncCog(bot))