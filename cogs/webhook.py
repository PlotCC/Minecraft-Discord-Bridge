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
from webhook_actions import open_latest_log, need_log_reopen, regex_action, multi_regex_action, action_list
import config

LOG = logging.getLogger("WEBHOOK_COG")

emoji_match = "<a?(:.*?:)\d*?>"
def parse_emoji(content):
    return emoji.demojize(re.sub(emoji_match, "\1", content))

def setup_action(callback, what_do: str):
    LOG.debug(f"  Event: '{callback.__name__}'")
    LOG.debug(f"    Action: {what_do}")
    LOG.debug(f"    Enabled: {config.webhook['actions_enabled'][callback.__name__]}")
    LOG.debug(f"    Regex: {config.webhook['regex'][callback.__name__]}")

    return regex_action(config.webhook["regex"][callback.__name__], callback)

def setup_multi_action(callbacks, what_do: str):
    LOG.debug(f"  Multi-event:")
    LOG.debug(f"    Action: {what_do}")
    for callback in callbacks:
        LOG.debug(f"    Event: '{callback.__name__}'")
        LOG.debug(f"      Regex: {config.webhook['regex'][callback.__name__]}")
        LOG.debug(f"      Enabled: {config.webhook['actions_enabled'][callback.__name__]}")

    return multi_regex_action([config.webhook["regex"][callback.__name__] for callback in callbacks], callbacks)

class WebhookCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="actions",
        description="Toggle a webhook action, allows to disable things like player join/leave events or etc.",
    )
    @app_commands.describe(action="The action to enable or disable.", enabled="Whether to enable or disable the action.")
    @app_commands.choices(action=[
        app_commands.Choice(name="player_message_reply", value=1),
        app_commands.Choice(name="player_message_noreply", value=2),
        app_commands.Choice(name="player_joined", value=3),
        app_commands.Choice(name="player_left", value=4),
        app_commands.Choice(name="server_starting", value=5),
        app_commands.Choice(name="server_started", value=6),
        app_commands.Choice(name="server_stopping", value=7),
        app_commands.Choice(name="server_list", value=8),
        app_commands.Choice(name="console_message", value=9),
        app_commands.Choice(name="advancement", value=10),
        app_commands.Choice(name="list-actions", value=11),
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def actions(self, interaction: discord.Interaction, action: app_commands.Choice[int], enabled: typing.Optional[bool]=None) -> None:
        LOG.info(f"Action [{action.name} ({action.value}) -> {enabled}] requested by {interaction.user.name}#{interaction.user.discriminator}.")
        if action.value == 10:
            await interaction.response.send_message("```" + "\n".join([_action.name for _action in self.action_list.all_actions]) + "```")
            return
        
        action_enabled = self.action_list.get_enabled(action.name)

        if enabled == None:
            await interaction.response.send_message(f"Action {action.name} is currently {'enabled' if action_enabled else 'disabled'}.")
            return
        
        if enabled:
            self.action_list.enable_action(action.name)
        else:
            self.action_list.disable_action(action.name)
        await interaction.response.send_message(f"Action {action.name} is now {'enabled' if enabled else 'disabled'}.")

    # Task that runs forever (only started once) that runs main from webhook.py
    async def run_webhook(self):
        try: # Wrap everything in a try since the error isn't propagated properly.
            async with aiohttp.ClientSession() as session:
                LOG.info("Connecting to webhook...")
                webhook = discord.Webhook.from_url(config.webhook["url"], session=session)
                LOG.info("Webhook connected.")
                whb = Bridge(webhook)  # Create the webhook bridge object.

                LOG.info("Setting up regexes.")

                LOG.info("The following regex actions are being registered:")

                self.action_list = self.setup_actions(whb)

                LOG.info("Done action setup.")

                f = open_latest_log()
                f.seek(0, 2)

                # Main loop: Grab a line of the file, check if it matches any patterns. If so, run the action.
                LOG.info(f"Listening to log file {config.webhook['latest_log_location']}.")
                while True:
                    line = f.readline()
                    if line:
                        if line != "" and line != "\n":
                            match = self.action_list.check(line)
                            if match:
                                await match[1](match[0])
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
        except Exception as e:
            LOG.error("Webhook task failed!")
            LOG.exception(e)
    
    def setup_actions(self, whb: Bridge):
        # Initial step: Add all actions to the list.
        list = []

        def insert_action(action: regex_action):
            list.insert(0, action)

        # Player chatted action
        async def player_message_noreply(match):
            LOG.info("Player message (no reply), sending...")
            await whb.on_player_message_noreply(match.group(1), match.group(2))
        
        async def player_message_reply(match):
            LOG.info("Player message (with reply), getting message from ID...")
            # match group 1 is the message ID
            # match group 2 is the ping status (literally "pingon" or "pingoff")
            # match group 3 is the player name
            # match group 4 is the message

            # Get the message from the ID
            message = None
            author = None
            ping_str = None
            try:
                message_d = await self.bot.bridge_channel.fetch_message(int(match.group(1)))
                author = message_d.author.display_name
                message = message_d.content
                ping_str = f"<@{author.id}>"
            except:
                LOG.warn(f"Failed to get message from ID {match.group(1)}.")
                author = ":warning:"
                message = "Failed to fetch original message."
                ping_str = ""
                

            await whb.on_player_message_reply(match.group(3), match.group(4), author, message, ping_str)

        insert_action(
            setup_multi_action(
                [player_message_reply, player_message_noreply],
                "Send messages that players send ingame to Discord.",
            ),
        )

        # Player join action
        async def player_joined(match):
            LOG.info("Player joined, sending...")
            await whb.on_player_join(match.group(1))

        insert_action(
            setup_action(
                player_joined,
                "Send player join events to Discord.",
            ),
        )

        # Player leave action
        async def player_left(match):
            LOG.info("Player left, sending...")
            await whb.on_player_leave(match.group(1))

        insert_action(
            setup_action(
                player_left,
                "Send player leave events to Discord.",
            ),
        )

        # Server starting action
        async def server_starting(match):
            LOG.info("Server starting, sending...")
            await whb.on_server_starting()

        insert_action(
            setup_action(
                server_starting,
                "Send server starting events to Discord.",
            ),
        )

        # Server started action
        async def server_started(match):
            LOG.info("Server started, sending...")
            await whb.on_server_started()

        insert_action(
            setup_action(
                server_started,
                "Send server started events to Discord.",
            ),
        )

        # Server stopping action
        async def server_stopping(match):
            LOG.info("Server stopping, sending...")
            await whb.on_server_stopping()

        insert_action(
            setup_action(
                server_stopping,
                "Send server stop events to Discord.",
            ),
        )

        # Server list action
        async def server_list(match):
            LOG.info("Server list sending...")
            await whb.on_server_list(match.group(1), match.group(2), match.group(3))

        insert_action(
            setup_action(
                server_list,
                "Send server list events to Discord.",
            ),
        )

        # Console message action
        async def console_message(match):
            LOG.info("Console message sending...")
            await whb.on_console_message(match.group(1))

        insert_action(
            setup_action(
                console_message,
                "Send console messages to Discord.",
            ),
        )

        # Advancement action
        async def advancement(match):
            LOG.info("Advancement sending...")
            await whb.on_advancement(match.group(1), match.group(2))

        insert_action(
            setup_action(
                advancement,
                "Send advancement events to Discord.",
            ),
        )

        # Second step: Create the actions object.
        actions = action_list(list)

        # Third step: Enable or disable actions based on the config.
        for action in actions.all_actions:
            if config.webhook["actions_enabled"][action.name]:
                actions.enable_action(action)
                LOG.info(f"  Action '{action}' enabled.")
            else:
                actions.disable_action(action)
                LOG.info(f"  Action '{action}' disabled.")

        return actions
    
    @commands.Cog.listener()
    async def on_ready(self):
        None

    async def cog_load(self):
        # Start the webhook task
        self.webhook_task = self.bot.loop.create_task(self.run_webhook())

    async def cog_unload(self):
        self.webhook_task.cancel()
        

async def setup(bot: discord.ext.commands.Bot):
    await bot.add_cog(WebhookCog(bot))