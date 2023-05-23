import asyncio
import os
import logging
import discord
import pathlib
import libtmux
from discord.ext import commands

import config

path = pathlib.Path(__file__)
BOT_SRC = str(path.parent.absolute())

logging.basicConfig(level=logging.INFO)

LOG = logging.getLogger("MAIN")

intents = discord.Intents.default()
intents.message_content = True

async def startup():
    # Initialize the bot
    bot = commands.Bot(
        intents=intents,
        command_prefix=commands.when_mentioned_or(config.bot["prefix"])
    )

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
    bot.console_pane = console_win.panes[0]

    # Create the pane for the bridge.
    bot.bridge_pane = console_win.split_window(attach=True)

    # Start the bridge.
    bot.bridge_pane.send_keys(config.programs["bridge"])

    async with bot:
        # Collect cogs and load them.
        for extension in [f.replace(".py","") for f in os.listdir(f"{BOT_SRC}/cogs") if os.path.isfile(os.path.join(f"{BOT_SRC}/cogs",f))]:
            LOG.info(f"Loading extension {extension}...")
            try:
                await bot.load_extension(f"cogs.{extension}")
            except Exception as e:
                LOG.exception(f"Failed to load extension {extension} because: {e}")
            else:
                LOG.info(f"Successfully loaded {extension}.")

        LOG.info("Loading Jishaku...")
        try:
            await bot.load_extension("jishaku")
        except Exception as e:
            LOG.exception(f"Failed to load Jishaku because: {e}")
        else:
            LOG.info("Successfully loaded Jishaku.")

        # Start the bot
        LOG.info("Starting bot.")
        
        await bot.start(config.bot["token"])

if __name__ == "__main__":
    asyncio.run(startup())
