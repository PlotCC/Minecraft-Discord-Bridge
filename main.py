import asyncio
import os
import logging
import discord
import pathlib
import libtmux
from discord.ext import commands
from discord import app_commands

import config

path = pathlib.Path(__file__)
BOT_SRC = str(path.parent.absolute())

# Copy the last bot-latest.log to bot-old.log, if it exists.
if os.path.isfile("bot-latest.log"):
    if os.path.isfile("bot-old.log"):
        os.remove("bot-old.log")
    os.rename("bot-latest.log", "bot-old.log")


logging.basicConfig(level=config.bot["logging_level"])
handler = logging.FileHandler(filename="bot-latest.log", encoding="utf-8", mode="w")
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logging.getLogger().addHandler(handler)

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

    session = None
    bot.session_existed = False

    try:
        # Create a new session. This throws if a session exists already!
        session = Server.new_session(config.tmux_data["tmux_session"])
    except:
        LOG.info("tmux session already exists. Joining to it instead.")
        for _session in Server.sessions:
            if _session.name == config.tmux_data["tmux_session"]:
                session = _session
                bot.session_existed = True
                break
    
    if not session:
        raise Exception("Tmux session existed but also it did not. Weird.")

    # Get the main window.
    console_win = session.windows[0]
    console_win.rename_window(config.tmux_data["window_name"])
    # Set the layout to look fancy.

    if not bot.session_existed: # Only set the layout if it wasn't already set.
        console_win.select_layout("main-vertical")

    # Get the console window pane.
    bot.console_pane = console_win.panes[0]

    # Block chat until the server is confirmed online.
    bot.block_chat = True

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
        
        LOG.info("Setting up cog error handler...")
        async def on_tree_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
            if isinstance(error, app_commands.CommandOnCooldown):
                return await interaction.response.send_message(f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.", ephemeral=True)
            elif isinstance(error, app_commands.MissingPermissions) or isinstance(error, app_commands.CheckFailure):
                return await interaction.response.send_message("You do not have the required permissions to run this command.", ephemeral=True)
            elif isinstance(error, app_commands.MissingRole):
                return await interaction.response.send_message("You do not have the required role to run this command.", ephemeral=True)
            elif isinstance(error, app_commands.CommandNotFound):
                return await interaction.response.send_message("Command not found.", ephemeral=True)
            else:
                await interaction.response.send_message("An error occurred.", ephemeral=True)
                raise error
        
        bot.tree.on_error = on_tree_error

        # Start the bot
        LOG.info("Starting bot.")
        
        await bot.start(config.bot["token"])

if __name__ == "__main__":
    asyncio.run(startup())
