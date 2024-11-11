import discord
from discord.ext import commands
from discord import app_commands
import logging

import config

LOG = logging.getLogger("SYNC")

def is_owner(interaction: discord.Interaction) -> bool:
    return interaction.user.id == config.bot["owner_id"]



class SyncCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



    @app_commands.command(name="resync", description="Properly re-synchronize the command tree, deleting old commands as well.")
    @app_commands.check(is_owner)
    async def resync(self, interaction: discord.Interaction) -> None:
        """
        Properly re-synchronize the command tree, deleting old commands as well.
        """

        LOG.info("Resyncing command tree...")

        # Delete all commands.
        for command in self.bot.walk_commands():
            try: await command.delete()
            except: pass
        
        # Re-register all commands.
        await self.bot.tree.sync()

        await interaction.response.send_message("Resynced command tree.")



async def setup(bot):
    await bot.add_cog(SyncCog(bot))