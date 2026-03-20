import discord
from discord.ext import commands
from discord import app_commands
import logging

import config
from discord_bot import DiscordBot
from privilege_test import check_permissions

LOG = logging.getLogger("BACKUP")


class AdministrationCog(commands.Cog):
    """
    This cog adds administration commands to the bot.
    """

    def __init__(self, bot: DiscordBot):
        self.bot: DiscordBot = bot


    
    @app_commands.command(
        name="about-me",
        description="Get information about yourself in the context of the bot."
    )
    @check_permissions(config.privileges.user)
    async def about_me(self, interaction: discord.Interaction) -> None:
        user_definitions = config.privileges.users
        user_id = interaction.user.id

        embed = discord.Embed(
            title="About Me",
            color=discord.Color.blue()
        )
        embed.add_field(name="Username", value=str(interaction.user), inline=False)
        embed.add_field(name="User ID", value=str(user_id), inline=False)
        embed.add_field(
            name="privilege Level",
            value=user_definitions.get(user_id, config.privileges.user).name.title(),
            inline=False
        )
        await interaction.response.send_message(embed=embed)



    @app_commands.command(
        name="lock-commands",
        description="Lock all commands to prevent their use. Only applies to people of lower privilege than you."
    )
    @check_permissions(config.privileges.moderator)
    async def lock_commands(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("This command is not yet implemented.")



    @commands.Cog.listener()
    async def on_ready(self):
        pass



    async def cog_load(self):
        pass



    async def cog_unload(self):
        pass



async def setup(bot):
    await bot.add_cog(AdministrationCog(bot))
