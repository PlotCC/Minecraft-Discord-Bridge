import aiohttp
import asyncio
import re
import discord
from discord import Webhook
import time

from webhook_bridge import Bridge
import config

class regex_action:
    """Holds a regex and runs a function if the regex matches an input string"""

    def __init__(self, regex:str, on_match, name:str):
        self.regex = regex
        self.on_match = on_match
        self.name = name

    def check(self, input:str):
        match = re.search(self.regex, input)
        if match:
            print(f"Got match ({self.name})!")
            return match

def print_action(regex:str, what_do:str):
    print(f"  Regex: '{regex}'\n    Action: {what_do}")

async def main():
    async with aiohttp.ClientSession() as session:
        print("Connecting to webhook...")
        webhook = Webhook.from_url(config.webhook["url"], session=session)
        print("Webhook connected.")
        whb = Bridge(webhook) # Create the webhook bridge object.
        
        print("Setting up regexes.")
        regexes = [] # stores all the regex actions

        print("The following regex actions are being registered:")

        # Player chatted action
        async def player_message(match):
            print("Player message, sending...")
            await whb.on_player_message(match.group(1), match.group(2))
        regexes.insert(0, regex_action(config.webhook["regex"]["player_message"], player_message, "Player message"))
        print_action(config.webhook["regex"]["player_message"], "Send messages that players send ingame to Discord.")

        # Player join action
        async def player_joined(match):
            print("Player joined, sending...")
            await whb.on_player_join(match.group(1))
        regexes.insert(0, regex_action(config.webhook["regex"]["player_joined"], player_joined, "Player joined"))
        print_action(config.webhook["regex"]["player_joined"], "Send player join events to Discord.")

        # Player leave action
        async def player_left(match):
            print("Player left, sending...")
            await whb.on_player_leave(match.group(1))
        regexes.insert(0, regex_action(config.webhook["regex"]["player_left"], player_left, "Player left"))
        print_action(config.webhook["regex"]["player_left"], "Send player leave events to Discord.")

        # Server starting action
        async def server_starting(match):
            print("Server starting, sending...")
            await whb.on_server_starting();
        regexes.insert(0, regex_action(config.webhook["regex"]["server_starting"], server_starting, "Server starting"))
        print_action(config.webhook["regex"]["server_starting"], "Send server starting events to Discord.")

        # Server started action
        async def server_started(match):
            print("Server started, sending...")
            await whb.on_server_started();
        regexes.insert(0, regex_action(config.webhook["regex"]["server_started"], server_started, "Server started"))
        print_action(config.webhook["regex"]["server_started"], "Send server started events to Discord.")

        # Server stopping action
        async def server_stopping(match):
            print("Server stopping, sending...")
            await whb.on_server_stopping();
        regexes.insert(0, regex_action(config.webhook["regex"]["server_stopping"], server_stopping, "Server stopping"))
        print_action(config.webhook["regex"]["server_stopping"], "Send server stop events to Discord.")

        print("Done action setup.")

        f = open(config.webhook["latest_log_location"])
        f.seek(0, 2)

        # Main loop: Grab a line of the file, check if it matches any patterns. If so, run the action.
        print("Listening to log file.")
        while 1:
            line = f.readline()
            if line:
                if line != "" and line != "\n":
                    # For each action
                    for action in regexes:
                        # If the action's regex matched
                        match = action.check(line)
                        if match:
                            # Run the action.
                            await action.on_match(match)
                            break
                elif line == "\n":
                    print("Ignored empty newline.")
            else:
                # Seek to the end of the file. This fixes freezing if the log file is cleared and reopened.
                f.seek(0, 2)
            
            # Delay between checking each line. I assume 10 lines per second is more than enough?
            # A better delay system will be set up soon, this is mostly temporary.
            time.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(main())
    # loop = asyncio.new_event_loop()
    # loop.run_until_complete(main())
    # loop.close()