# Small helper class for working with commands over rcon.

from aiomcrcon import Client

from config import server as server_config

class Rcon:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = None # Initialized in connect()

        return cls._instance

    def __init__(self):
        None

    async def connect(self):
        if self.client is None:
            self.client = Client(
                server_config["rcon_host"],
                server_config["rcon_port"],
                server_config["rcon_password"],
            )
        await self.client.connect()

    async def send(self, command: str):
        if not self.client:
            await self.connect()

        try:
            return await self.client.send_cmd(command)
        except BrokenPipeError:
            # Reset the client.
            self.client = None
            try:
                await self.connect()
                return await self.client.send_cmd(command)
            except Exception as e:
                return f"Failed to send command to server (after broken pipe): {e}", None
        except Exception as e:
            try:
                await self.connect()
                return await self.client.send_cmd(command)
            except Exception as e2:
                return f"Failed to send command to server: {e}\nWhile attempting to reconnect, another exception was raised: {e2}", None

    async def close(self):
        if self.client:
            await self.client.close()
            self.client = None