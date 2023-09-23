import aiohttp
import asyncio
import re
from discord import Webhook
import time
import os

from webhook_bridge import Bridge
import config

filesize = 0


def need_log_reopen():
    global filesize
    if not os.path.isfile(config.webhook["latest_log_location"]):
        print("Reopen required.")
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
            print(f"Waiting for latest.log to exist ({lll}).")
        printed = True
        time.sleep(0.1)

    print("Log opened.")
    return open(lll)


class regex_action:
    """Holds a regex and runs a function if the regex matches an input string"""

    def __init__(self, regex: str, on_match, name: str):
        self.regex = regex
        self.on_match = on_match
        self.name = name

    def check(self, input: str):
        match = re.search(self.regex, input)
        if match:
            print(f"Got match ({self.name})!")
            return match

def setup_action(callback: function, what_do: str):
    print(
        f"  Event: '{callback.__name__}'\n    Action: {what_do}\n    Enabled: {config.webhook['actions_enabled'][callback.__name__]}\n"
    )
    return regex_action(config.webhook["regex"][callback.__name__], callback, what_do)


def setup_actions(whb: Bridge):
    actions = []

    def insert_action(action: regex_action):
        if config.webhook["actions_enabled"][action.name]:
            actions.insert(0, action)

    # Player chatted action
    async def player_message(match):
        print("Player message, sending...")
        await whb.on_player_message(match.group(1), match.group(2))

    insert_action(
        setup_action(
            player_message,
            "Send messages that players send ingame to Discord.",
        ),
    )

    # Player join action
    async def player_joined(match):
        print("Player joined, sending...")
        await whb.on_player_join(match.group(1))

    insert_action(
        setup_action(
            player_joined,
            "Send player join events to Discord.",
        ),
    )

    # Player leave action
    async def player_left(match):
        print("Player left, sending...")
        await whb.on_player_leave(match.group(1))

    insert_action(
        setup_action(
            player_left,
            "Send player leave events to Discord.",
        ),
    )

    # Server starting action
    async def server_starting(match):
        print("Server starting, sending...")
        await whb.on_server_starting()

    insert_action(
        setup_action(
            server_starting,
            "Send server starting events to Discord.",
        ),
    )

    # Server started action
    async def server_started(match):
        print("Server started, sending...")
        await whb.on_server_started()

    insert_action(
        setup_action(
            server_started,
            "Send server started events to Discord.",
        ),
    )

    # Server stopping action
    async def server_stopping(match):
        print("Server stopping, sending...")
        await whb.on_server_stopping()

    insert_action(
        setup_action(
            server_stopping,
            "Send server stop events to Discord.",
        ),
    )

    # Server list action
    async def server_list(match):
        print("Server list sending...")
        await whb.on_server_list(match.group(1), match.group(2), match.group(3))

    insert_action(
        setup_action(
            server_list,
            "Send server list events to Discord.",
        ),
    )

    # Console message action
    async def console_message(match):
        print("Console message sending...")
        await whb.on_console_message(match.group(1))

    insert_action(
        setup_action(
            console_message,
            "Send console messages to Discord.",
        ),
    )

    # Advancement action
    async def advancement(match):
        print("Advancement sending...")
        await whb.on_advancement(match.group(1), match.group(2))

    insert_action(
        setup_action(
            advancement,
            "Send advancement events to Discord.",
        ),
    )

    return actions


async def main():
    async with aiohttp.ClientSession() as session:
        print("Connecting to webhook...")
        webhook = Webhook.from_url(config.webhook["url"], session=session)
        print("Webhook connected.")
        whb = Bridge(webhook)  # Create the webhook bridge object.

        print("Setting up regexes.")

        print("The following regex actions are being registered:")

        regexes = setup_actions(whb)

        print("Done action setup.")

        f = open_latest_log()
        f.seek(0, 2)

        # Main loop: Grab a line of the file, check if it matches any patterns. If so, run the action.
        print(f"Listening to log file {config.webhook['latest_log_location']}.")
        while True:
            line = f.readline()
            if line:
                if line != "" and line != "\n":
                    # For each action
                    for action in regexes:
                        # If the action's regex matched
                        match = action.check(line)
                        if match:
                            # Run the action.
                            print(f"Match: {line}")
                            await action.on_match(match)
                            break
                elif line == "\n":
                    print("Ignored empty newline.")
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
