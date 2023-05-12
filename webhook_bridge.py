import discord
import requests

import config

class Bridge:
    def __init__(self, webhook:discord.Webhook):
        self.webhook = webhook
        self.username_cache = dict()

    async def __send_player_message(self, username:str, message="", embed=None):
        avatar_url = None
        if username not in self.username_cache:
            # get the UUID of the player:
            print(f"Attempt to cache username: {username}")
            uuid_response = requests.get(config.icons["uuid_lookup_url"] + username, verify="consolidate.pem")
            if uuid_response.status_code == 200:
                uuid_json = uuid_response.json()
                print(f"200. UUID: {uuid_json['id']}")
                print(f"Avatar url: {config.icons['avatar_lookup_url'] + uuid_json['id']}" + ".png?size=128&default=MHF_Steve")
                self.username_cache[username] = config.icons["avatar_lookup_url"] + uuid_json["id"] + ".png?size=128&default=MHF_Steve"
                avatar_url = self.username_cache[username]
        else:
            avatar_url = self.username_cache[username]

        await self.webhook.send(content=message, embed=embed, username=username, avatar_url=avatar_url)
    
    async def __send_server_message(self, message="", embed=None):
        await self.webhook.send(content=message, embed=embed, username=config.webhook["server_name"], avatar_url = config.icons["minecraft"])
    
    async def on_player_message(self, username:str, message:str):
        await self.__send_player_message(username, message=message)

    async def on_player_join(self, username:str):
        embed = discord.Embed(color=0x00ff00, description=":inbox_tray: **" + username + "** joined the game.")

        await self.__send_server_message(embed=embed)

    async def on_player_leave(self, username:str):
        embed = discord.Embed(color=0xff0000, description=":outbox_tray: **" + username + "** left the game.")

        await self.__send_server_message(embed=embed)