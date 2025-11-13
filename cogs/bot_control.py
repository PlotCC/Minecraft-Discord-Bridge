import discord
from discord.ext import commands, tasks
import logging
import asyncio

import config
from discord_bot import DiscordBot

LOG = logging.getLogger("BACKUP")


class BotControlCog(commands.Cog):
    """
    This cog controls various aspects of the bot.
    """

    def __init__(self, bot: DiscordBot):
        self.bot: DiscordBot = bot


    
    @tasks.loop(seconds=60)
    async def update_server_status(self):
        try:
            await self.bot.rcon.send_server_command("list")
        except:
            pass

        # Give just enough time for the server to respond.
        await asyncio.sleep(1)

        if hasattr(self.bot, "players_online"):
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.playing,
                    name=config.server.name,
                    state=f"{self.bot.players_online if self.bot.players_online else 0} player{'' if self.bot.players_online == 1 else 's'} online"
                )
            )
        else:
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.playing,
                    name=config.server.name
                )
            )



    @commands.Cog.listener()
    async def on_ready(self):
        self.update_server_status.start()



    async def cog_load(self):
        pass



    async def cog_unload(self):
        self.update_server_status.stop()



async def setup(bot):
    await bot.add_cog(BotControlCog(bot))
