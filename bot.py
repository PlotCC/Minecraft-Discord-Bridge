# Discord bot to act as a bridge between MC servers.

from minecraftTellrawGenerator import MinecraftTellRawGenerator as tellraw
import schedule
import discord
import asyncio
import libtmux
import time
import zmq

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

    # Lock out the server console when the server is not running
    server_lock = True

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
        if message.author == client.user:
            return
        
        if message.author.bot:
            return
                
        if message.channel.id != config.bot["channel_id"]:
            echo(f"Received message in incorrect channel.")
            return
        
        if server_lock:
            return

        echo(f"Received message: [{message.author.display_name}]: {message.content}")
        a = tellraw(
            text = "["
        )
        b = tellraw(
            text="Discord",
            color="blue",
            hover=tellraw(text="This message was sent from Discord!", color="light_purple"),
            bold=True
        )
        c = tellraw(
            text = "] "
        )
        d = None
        if config.webhook["insertion_available"]:
            d = tellraw(
                text=message.author.display_name,
                insertion="<@" + str(message.author.id) + "> ",
                hover=tellraw(text="Click to reply!", color="yellow")
            )
            
        else:
            d = tellraw(
                text=message.author.display_name,
                insertion="<@" + str(message.author.id) + "> ",
                hover=tellraw(text=message.author.mention, color="yellow")
            )
        e = tellraw(
            text=": " + message.content
        )

        combined = tellraw.multiple_tellraw(a, b, c, d, e)
        console_pane.send_keys("tellraw @a " + combined)
        echo(f"Tellraw sent to server: {combined}")
    
    @client.event
    async def on_message_edit(before, after):
        if before.author == client.user:
            return
        
        if before.author.bot:
            return
        
        if before.channel.id != config.bot["channel_id"]:
            echo(f"Received edit in incorrect channel.")
            return
        
        if server_lock:
            return
        
        echo(f"Edit detected.")
        echo(f"Before: {before.content}")
        echo(f"After : {after.content}")

        a = tellraw(
            text="["
        )
        b = tellraw(
            text="Discord",
            color="blue",
            hover=tellraw(text="This message was sent from Discord!", color="light_purple"),
            bold=True
        )
        c = tellraw(
            text="] "
        )
        d = tellraw(
            text="[EDIT - OLD] ",
            color="dark_gray",
            italic=True
        )
        e = tellraw(
            text=before.author.display_name,
            color="dark_gray",
            italic=True
        )
        
        f = tellraw(
            text=": " + before.content,
            hover=tellraw(text="This is an edit of a previous message."),
            color="dark_gray",
            italic=True
        )

        combined = tellraw.multiple_tellraw(a, b, c, d, e, f)
        console_pane.send_keys("tellraw @a " + combined)
        echo(f"Tellraw sent to server: {combined}")

        a = tellraw(
            text = "["
        )
        b = tellraw(
            text="Discord",
            color="blue",
            hover=tellraw(text="This message was sent from Discord!", color="light_purple"),
            bold=True
        )
        c = tellraw(
            text="] "
        )
        d = tellraw(
            text="[EDIT - NEW] ",
            color="gold"
        )
        e = tellraw(
            text=after.author.display_name,
            color="gold"
        )
        
        f = tellraw(
            text=": ",
            color="gold"
        )

        g = tellraw(
            text=after.content,
            color="gold"
        )

        combined = tellraw.multiple_tellraw(a, b, c, d, e, f, g)
        console_pane.send_keys("tellraw @a " + combined)
        echo(f"Tellraw sent to server: {combined}")

    loop = asyncio.get_event_loop()

    async def run_bot():
        try:
            await client.run(config.bot["token"])
        except Exception as e:
            await client.close()
            echo("Error occurred!")
    
    def get_time_string(time_left:int):
        hours = time_left / 3600
        time_left %= 3600
        minutes = time_left / 60
        time_left %= 60
        seconds = time_left

        if hours > 0 and minutes == 0 and seconds == 0:
            return tellraw.multiple_tellraw(
                tellraw(text="Automatic server restart in ", color="yellow"),
                tellraw(text=str(hours) + (" hours" if hours > 1 else " hour"), color="gold"),
                tellraw(text=".", color="yellow")
            )
        if hours == 0 and minutes == 30 and seconds == 0:
            return tellraw.multiple_tellraw(
                tellraw(text="Automatic server restart in ", color="yellow"),
                tellraw(text="30 minutes", color="gold"),
                tellraw(text=".", color="yellow")
            )
        if hours == 0 and minutes == 10 and seconds == 0:
            return tellraw.multiple_tellraw(
                tellraw(text="Automatic server restart in ", color="yellow"),
                tellraw(text="10 minutes", color="gold"),
                tellraw(text=".", color="yellow")
            )
        if hours == 0 and minutes == 5 and seconds == 0:
            return tellraw.multiple_tellraw(
                tellraw(text="Automatic server restart in ", color="yellow"),
                tellraw(text="5 minutes", color="gold"),
                tellraw(text=".", color="yellow")
            )
        if hours == 0 and minutes == 1 and seconds == 0:
            return tellraw.multiple_tellraw(
                tellraw(text="Automatic server restart in ", color="yellow"),
                tellraw(text="1 minute", color="gold"),
                tellraw(text=".", color="yellow")
            )
        if hours == 0 and minutes == 0 and seconds == 30:
            return tellraw.multiple_tellraw(
                tellraw(text="Automatic server restart in ", color="yellow"),
                tellraw(text="30 seconds", color="gold"),
                tellraw(text=".", color="yellow")
            )
        if hours == 0 and minutes == 0 and seconds <= 10:
            return tellraw.multiple_tellraw(
                tellraw(text="Automatic server restart in ", color="yellow"),
                tellraw(text=str(seconds) + (" seconds" if seconds > 1 else " second"), color="gold"),
                tellraw(text=".", color="yellow")
            )
        # No return otherwise.

    def server_restart():
        if config.server["do_automatic_restart"]:
            for i in range(config.server["restart_time"], -1, -1):
                output = get_time_string(i)
                if output:
                    console_pane.send_keys(output)
                time.sleep(1)

            # console_pane.send_keys("tellraw @a " + tellraw(text="Server restarting...", bold=True, color="red"))
            time.sleep(0.5)
            console_pane.send_keys("stop")

            time.sleep(60)
            # TODO: Determine if there is a way to see when the server actually 
            # stops, instead of just waiting some amount of time and hoping it's
            # done.
            console_pane.send_keys(config.programs["minecraft"])


    async def scheduler():
        config.server["restart_schedule"].do(server_restart)

        while True:
            schedule.run_pending()
            time.sleep(1)

    async def thread_run():
        asyncio.run_coroutine_threadsafe(scheduler(), loop)

    async def main():
        await asyncio.gather(
            run_bot(),
            asyncio.to_thread(thread_run)
        )

    # Start the minecraft server.
    console_pane.send_keys(config.programs["minecraft"])
    server_lock = False

    # Run the bot.
    loop.run_until_complete(main())

    # Cleanup: Stop the tmux sessions.
    print("Dude has stopped bro")

    # Close the echo server and client.
    echo("__close__")
    socket.close()
