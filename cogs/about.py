import discord
from discord.ext import commands
from discord import app_commands
import logging

import config
from discord_bot import DiscordBot

LOG = logging.getLogger("BACKUP")


class AboutCog(commands.Cog):
    """
    This cog allows users to get information about themselves in the context of the bot.
    """

    def __init__(self, bot: DiscordBot):
        self.bot: DiscordBot = bot


    
    @app_commands.command(
        name="about-me",
        description="Get information about yourself in the context of the bot."
    )
    async def about_me(self, interaction: discord.Interaction) -> None:
        user_definitions = config.priveleges.users
        user_id = interaction.user.id

        embed = discord.Embed(
            title="About Me",
            color=discord.Color.blue()
        )
        embed.add_field(name="Username", value=str(interaction.user), inline=False)
        embed.add_field(name="User ID", value=str(user_id), inline=False)
        embed.add_field(
            name="Privelege Level",
            value=user_definitions.get(user_id, config.priveleges.user).name.title(),
            inline=False
        )
        await interaction.response.send_message(embed=embed)



    @commands.Cog.listener()
    async def on_ready(self):
        pass



    async def cog_load(self):
        pass



    async def cog_unload(self):
        pass



async def setup(bot):
    await bot.add_cog(AboutCog(bot))
