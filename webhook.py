import aiohttp
import asyncio
import re
from discord import Webhook
import time
import os
import logging

from webhook_bridge import Bridge
import config

filesize = 0

LOG = logging.getLogger("WEBHOOK")

def need_log_reopen():
    global filesize
    if not os.path.isfile(config.webhook["latest_log_location"]):
        LOG.info("Reopen required.")
        return True
    new_size = os.path.getsize(config.webhook["latest_log_location"])
    old_size = filesize
    filesize = new_size

    return new_size < old_size


def open_latest_log():
    printed = False
    lll = config.webhook["latest_log_location"]
    while not os.path.isfile(lll):
        if not printed:
            LOG.info(f"Waiting for latest.log to exist ({lll}).")
        printed = True
        time.sleep(0.1)

    LOG.info("Log opened.")
    return open(lll)


class regex_action:
    """Holds a regex and runs a function if the regex matches an input string"""

    def __init__(self, regex: str, on_match):
        self.regex = regex
        self.on_match = on_match
        self.name = on_match.__name__

    def check(self, input: str):
        match = re.search(self.regex, input)
        if match:
            LOG.debug(f"Got match ({self.name})!")
            return match

class action_list:
    """
        Holds a list of regex_actions and checks them all for matches given an input string.
        Grants the ability to dynamically enable and/or disable actions.
    """
    
    def __init__(self, actions: list):
        self.all_actions = actions
        self.enabled_actions = []
        self.disabled_actions = []
    
    # Find the first action that matches the input string, return it and the match.
    def check(self, input: str):
        for action in self.enabled_actions:
            match = action.check(input)
            if match:
                return (action, match)
        
        return None # Just here so we can note that if it fails it returns nothing.
    
    # Enable an action by name.
    def enable_action(self, name: str):
        for action in self.disabled_actions:
            if action.name == name:
                self.enabled_actions.append(action)
                self.disabled_actions.remove(action)
                return
        
        for action in self.all_actions:
            if action.name == name:
                self.enabled_actions.append(action)
                return
    
    # Disable an action by name.
    def disable_action(self, name: str):
        for action in self.enabled_actions:
            if action.name == name:
                self.disabled_actions.append(action)
                self.enabled_actions.remove(action)
                return
        
        for action in self.all_actions:
            if action.name == name:
                self.disabled_actions.append(action)
                return
    
    # Enable all actions.
    def enable_all(self):
        self.enabled_actions = self.all_actions
        self.disabled_actions = []
    
    # Disable all actions.
    def disable_all(self):
        self.disabled_actions = self.all_actions
        self.enabled_actions = []

def setup_action(callback, what_do: str):
    LOG.debug(
        f"  Event: '{callback.__name__}'\n    Action: {what_do}\n    Enabled: {config.webhook['actions_enabled'][callback.__name__]}\n    Regex: {config.webhook['regex'][callback.__name__]}\n"
    )
    return regex_action(config.webhook["regex"][callback.__name__], callback)


def setup_actions(whb: Bridge):
    # Initial step: Add all actions to the list.
    list = []

    def insert_action(action: regex_action):
        list.insert(0, action)

    # Player chatted action
    async def player_message(match):
        LOG.info("Player message, sending...")
        await whb.on_player_message(match.group(1), match.group(2))

    insert_action(
        setup_action(
            player_message,
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
            actions.enable_action(action.name)
            LOG.info(f"  Action '{action.name}' enabled.")
        else:
            actions.disable_action(action.name)
            LOG.info(f"  Action '{action.name}' disabled.")

    return actions


async def main():
    async with aiohttp.ClientSession() as session:
        LOG.info("Connecting to webhook...")
        webhook = Webhook.from_url(config.webhook["url"], session=session)
        LOG.info("Webhook connected.")
        whb = Bridge(webhook)  # Create the webhook bridge object.

        LOG.info("Setting up actions.")

        LOG.debug("The following actions are being registered:")

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
                    LOG.debug("Ignored empty newline.")
                elif line == "":
                    if need_log_reopen():
                        f = open_latest_log()
            else:
                if need_log_reopen():
                    f = open_latest_log()

            # Delay between checking each line. I assume 100 lines per second is more than enough?
            # A better delay system will be set up soon, this is mostly temporary.
            await asyncio.sleep(0.01)


if __name__ == "__main__":
    asyncio.run(main())
