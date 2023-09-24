import re
import discord
import emoji
from discord.ext import commands
from discord import app_commands
import asyncio
import aiohttp
import logging
import typing

from webhook_bridge import Bridge
from webhook_actions import open_latest_log, need_log_reopen, setup_actions
import config

LOG = logging.getLogger("WEBHOOK_COG")

emoji_match = "<a?(:.*?:)\d*?>"
def parse_emoji(content):
    return emoji.demojize(re.sub(emoji_match, "\1", content))

class WebhookCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="actions",
        description="Toggle a webhook action, allows to disable things like player join/leave events or etc.",
    )
    @app_commands.describe(action="The action to enable or disable.", enabled="Whether to enable or disable the action.")
    @app_commands.choices(colors=[
        app_commands.Choice(name="player_message", value=1),
        app_commands.Choice(name="player_joined", value=2),
        app_commands.Choice(name="player_left", value=3),
        app_commands.Choice(name="server_starting", value=4),
        app_commands.Choice(name="server_started", value=5),
        app_commands.Choice(name="server_stopping", value=6),
        app_commands.Choice(name="server_list", value=7),
        app_commands.Choice(name="console_message", value=8),
        app_commands.Choice(name="advancement", value=9),
        app_commands.Choice(name="list-actions", value=10),
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def actions(self, interaction: discord.Interaction, action: app_commands.Choices[int], enabled: typing.Optional[str]=None) -> None:
        LOG.info(f"Action {action.name} ({action.value}) requested by {interaction.user.name}#{interaction.user.discriminator}.")

    # Task that runs forever (only started once) that runs main from webhook.py
    async def run_webhook(self):
        async with aiohttp.ClientSession() as session:
            LOG.info("Connecting to webhook...")
            webhook = discord.Webhook.from_url(config.webhook["url"], session=session)
            LOG.info("Webhook connected.")
            whb = Bridge(webhook)  # Create the webhook bridge object.

            LOG.info("Setting up regexes.")

            LOG.info("The following regex actions are being registered:")

            actions = setup_actions(whb)

            LOG.info("Done action setup.")

            f = open_latest_log()
            f.seek(0, 2)

            # Main loop: Grab a line of the file, check if it matches any patterns. If so, run the action.
            LOG.info(f"Listening to log file {config.webhook['latest_log_location']}.")
            while True:
                line = f.readline()
                if line:
                    if line != "" and line != "\n":
                        match = actions.check(line)
                        if match:
                            await match[0].on_match(match[1])
                    elif line == "\n":
                        LOG.info("Ignored empty newline.")
                    elif line == "":
                        if need_log_reopen():
                            f = open_latest_log()
                else:
                    if need_log_reopen():
                        f = open_latest_log()

                # Delay between checking each line. I assume 100 lines per second is more than enough?
                # A better delay system will be set up soon, this is mostly temporary.
                await asyncio.sleep(0.01)
    
    @commands.Cog.listener()
    async def on_ready(self):
        # Start the webhook task
        self.bot.loop.create_task(self.run_webhook())

    async def cog_load(self):
        None

    async def cog_unload(self):
        None
        

async def setup(bot: discord.ext.commands.Bot):
    await bot.add_cog(WebhookCog(bot))