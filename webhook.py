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
    print(f"  Regex: {regex}\n    Action: {what_do}")

async def main():
    async with aiohttp.ClientSession() as session:
        print("Connecting to webhook...")
        webhook = Webhook.from_url(config.webhook["url"], session=session)
        print("Webhook connected.")
        whb = Bridge(webhook)
        
        print("Setting up regexes.")

        regexes = []

        print("The following regex actions are being registered:")

        async def player_message(match):
            print("Player message, sending...")
            await whb.on_player_message(match.group(1), match.group(2))
        regexes.insert(0, regex_action(config.webhook["regex"]["player_message"], player_message, "Player message"))
        print_action(config.webhook["regex"]["player_message"], "Send messages that players send ingame to Discord.")

        async def player_joined(match):
            print("Player joined, sending...")
            await whb.on_player_join(match.group(1))
        regexes.insert(0, regex_action(config.webhook["regex"]["player_joined"], player_joined, "Player joined"))
        print_action(config.webhook["regex"]["player_joined"], "Send player join events to Discord.")

        async def player_left(match):
            print("Player left, sending...")
            await whb.on_player_leave(match.group(1))
        regexes.insert(0, regex_action(config.webhook["regex"]["player_left"], player_left, "Player left"))
        print_action(config.webhook["regex"]["player_left"], "Send player leave events to Discord.")

        print("Done regex stuff.")

        f = open(config.webhook["latest_log_location"])
        f.seek(0, 2)


        print("Listening to log file.")
        while 1:
            line = f.readline()
            if line:
                if line != "" and line != "\n":
                    for action in regexes:
                        match = action.check(line)
                        if match:
                            await action.on_match(match)
                            break
                elif line == "\n":
                    print("Ignored empty newline.")
            else:
                f.seek(0, 2)
            
            time.sleep(0.1)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.close()