import discord
import requests

import config

class Bridge:
    """A simple class which holds some methods for interacting with the webhook."""
    def __init__(self, webhook:discord.Webhook):
        self.webhook = webhook
        self.username_cache = dict()

    # Send a message which is "from" a player.
    async def __send_player_message(self, username:str, message="", embed=None):
        avatar_url = None

        # If we haven't already cached their avatar icon, grab the icon.
        if username not in self.username_cache:
            # get the UUID of the player
            print(f"Attempt to cache username: {username}")
            uuid_response = requests.get(config.icons["uuid_lookup_url"] + username)
            if uuid_response.status_code == 200:
                uuid_json = uuid_response.json()
                print(f"200. UUID: {uuid_json['id']}")
                print(f"Avatar url: {config.icons['avatar_lookup_url'] + uuid_json['id']}" + ".png?size=128&default=MHF_Steve")
                self.username_cache[username] = config.icons["avatar_lookup_url"] + uuid_json["id"] + ".png?size=128&default=MHF_Steve"
                avatar_url = self.username_cache[username]
        else:
            # If it is cached, just use that.
            avatar_url = self.username_cache[username]

        # If it is not cached and fails to get the avatar url, it will just pass an empty url to it.

        await self.webhook.send(content=message, embed=embed, username=username, avatar_url=avatar_url, allowed_mentions=discord.AllowedMentions(everyone=False))
    
    # Send a message to discord "from" the server.
    async def __send_server_message(self, message="", embed=None):
        await self.webhook.send(content=message, embed=embed, username=config.webhook["server_name"], avatar_url = config.icons["minecraft"], allowed_mentions=discord.AllowedMentions(everyone=False))
    
    # Send a player chat to discord.
    async def on_player_message(self, username:str, message:str):
        await self.__send_player_message(username, message=message)

    # Send a player join event to discord.
    async def on_player_join(self, username:str):
        embed = discord.Embed(color=0x00ff00, description=f":inbox_tray: **{username}** joined the game.")

        await self.__send_server_message(embed=embed)

    # Send a player leave event to discord.
    async def on_player_leave(self, username:str):
        embed = discord.Embed(color=0xff0000, description=f":outbox_tray: **{username}** left the game.")

        await self.__send_server_message(embed=embed)
    
    # Send a server starting event to discord.
    async def on_server_starting(self):
        embed = discord.Embed(color=0xccdd00, description=":yellow_circle: **The server is starting up...**")

        await self.__send_server_message(embed=embed)
    
    # Send a server starting event to discord.
    async def on_server_started(self):
        embed = discord.Embed(color=0x55dd55, description=":green_circle: **The server has started.**")

        await self.__send_server_message(embed=embed)
    
    # Send a server starting event to discord.
    async def on_server_stopping(self):
        embed = discord.Embed(color=0xdd5555, description=":red_circle: **The server has closed.**")

        await self.__send_server_message(embed=embed)

    # Send a server list event to discord.
    async def on_server_list(self, current:str, max:str):
        embed = discord.Embed(color=0x00ccff, description=f":information_source: **There are {current}/{max} players online currently.**")

        await self.__send_server_message(embed=embed)

    
    
