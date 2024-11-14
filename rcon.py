# Small helper class for working with commands over rcon.

from aiomcrcon import Client
import asyncio

from config import server as server_config

class QueueWithResult:
    def __init__(self, process_item):
        self._queue = asyncio.Queue()
        self._process_item = process_item
        self._processing_task = None



    async def add_to_queue(self, item):
        # Create a future to hold the result
        result_future = asyncio.get_running_loop().create_future()
        # Put the item and the future in the queue
        await self._queue.put((item, result_future))
        
        # Start processing if not already running
        if self._processing_task is None or self._processing_task.done():
            self._processing_task = asyncio.create_task(self._process_queue())
        
        return await result_future  # Wait for the result



    async def _process_queue(self):
        # Process items in the queue until it’s empty
        while not self._queue.empty():
            item, result_future = await self._queue.get()
            try:
                result = await self._process_item(item)  # Process item and get result
                result_future.set_result(result)  # Set the result in the future
            except Exception as e:
                result_future.set_exception(e)  # Handle any exceptions
            finally:
                self._queue.task_done()  # Mark the item as done



class Rcon:
    _instance = None



    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = None # Initialized in connect()
            cls._instance.queue = QueueWithResult(cls._instance._send)

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



    async def _send(self, command: str):
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



    async def send(self, command: str):
        return await self.queue.add_to_queue(command)



    async def close(self):
        if self.client:
            await self.client.close()
            self.client = None