# Discord bot to act as a bridge between MC servers.

import discord
import libtmux
import zmq
import time

import config

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

if __name__ == "__main__":
    # Get the tmux server object.
    Server = libtmux.Server()

    # Create a new session. This throws if a session exists already!
    session = Server.new_session(config.tmux_data["tmux_session"])

    # Get the main window.
    console_win = session.windows[0]
    console_win.rename_window(config.tmux_data["window_name"])
    # Set the layout to look fancy.
    console_win.select_layout("main-vertical")

    # Get the console window pane.
    console_pane = console_win.panes[0]

    # Create the pane for the bridge.
    bridge_pane = console_win.split_window(attach=True)

    # Start the bridge.
    bridge_pane.send_keys(config.programs["bridge"])

    # Create a pane for the echo system.
    echo_pane = console_win.split_window(attach=True)

    # Start the echo client.
    echo_pane.send_keys(config.programs["echo"])

    # The echo program should be running, though we'll give it a bit to start just to be sure.
    print("Waiting for echo to be ready (5 seconds).")
    time.sleep(5)
    
    # Connect to the echo server.
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(config.echo["connect"])
    def echo(*args):
        socket.send(str.encode(" ".join(args)))
        socket.recv() # Void the acknowledgement.
    
    echo("Echo server initialized.")

    # Setup all the discord event stuff.
    @client.event
    async def on_ready():
        echo(f"We have logged in as {client.user}")
        channel = client.get_channel(config.bot["channel_id"]) 
        await channel.send("Bridge started.")

    @client.event
    async def on_message(message):
        print(f"Received message: {message}")
        if message.author == client.user:
            return
                
        if message.channel.id != config.bot["channel_id"]:
            return
                
        if message.content == "bruh" or message.content == "Bruh":
            await message.channel.send("Bruh")

    # Start the minecraft server.
    console_pane.send_keys(config.programs["minecraft"])

    # Run the bot.
    client.run(config.bot["token"])

    # Cleanup: Stop the tmux sessions.
    print("Dude has stopped bro")
