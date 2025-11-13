import discord
from discord.ext import commands, tasks
from discord import app_commands
import logging
import asyncio

import config
import privilege_test

LOG = logging.getLogger("BACKUP")


class UserCog(commands.Cog):
    """
    This cog registers commands that the user can use to get 
    information about themselves.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot



    @app_commands.command(
        name="whoami",
        description="Get information about yourself."
    )
    async def whoami(self, interaction: discord.Interaction) -> None:
        """
        Get information about yourself.
        """
        if not privilege_test.test(interaction, config.privileges.user):
            await interaction.response.send_message(privilege_test.reject_message(config.privileges.user))
            return

        user = interaction.user
        user_id = user.id
        user_level = config.privileges.users.get(user_id, config.privileges.user)

        embed = discord.Embed(
            title="Who Am I?",
            color=discord.Color.blue()
        )
        embed.add_field(name="Username", value=str(user), inline=False)
        embed.add_field(name="User ID", value=str(user_id), inline=False)
        embed.add_field(name="Privilege Level", value=user_level.name.title(), inline=False)

        await interaction.response.send_message(embed=embed)



    @commands.Cog.listener()
    async def on_ready(self):
        pass



    async def cog_load(self):
        pass



    async def cog_unload(self):
        LOG.info("User cog is unloading.")



async def setup(bot):
    await bot.add_cog(UserCog(bot))