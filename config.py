import datetime
from zoneinfo import ZoneInfo

bot = dict(
    channel_id = 0,
    token = "",
    prefix = ">>"
)

server = dict(
    do_automatic_restart = True,
    restart_time = datetime.time(hour=0, minute=0, second=0, tzinfo=ZoneInfo("America/Edmonton"))
)

tmux_data = dict(
    tmux_session = "plotworld_server",
    window_name ="console",
)

webhook = dict(
    url = "",
    regex = dict(
        player_message = "^\[\d\d:\d\d:\d\d] \[Server thread\/INFO\] \[net\.minecraft\.server\.dedicated\.DedicatedServer\]: \[(?!P2).*?\] (.*?): (.+)$", # Should return two match groups -- playername and message.
        player_joined = "^\[\d\d:\d\d:\d\d\] \[Server thread\/INFO\] \[net\.minecraft\.server\.dedicated\.DedicatedServer\]: (.*?) joined the game$", # Should return a single match group -- playername.
        player_left = "^\[\d\d:\d\d:\d\d\] \[Server thread\/INFO\] \[net\.minecraft\.server\.dedicated\.DedicatedServer\]: (.*?) left the game$", # Should return a single match group -- playername.
        server_starting = "^\[\d\d:\d\d:\d\d\] \[main\/INFO\] \[FML\]: Forge Mod Loader version \d*?\.\d*?\.\d*?\.\d*? for Minecraft \d*?\.\d*?\.\d*? loading$", # No groups required.
        server_started = "^\[\d\d:\d\d:\d\d\] \[Server thread\/INFO\] \[Dynmap\]: \[Dynmap\] Enabled$", # No groups required.
        server_stopping = "^\[\d\d:\d\d:\d\d\] \[Server thread\/INFO\] \[net\.minecraft\.server\.MinecraftServer\]: Stopping server$", # No groups required.
        server_list = "^\[\d\d:\d\d:\d\d\] \[pool\-\d\-thread\-\d\/INFO\] \[minecraft\/DedicatedServer\]: ============ There are (\d+)\/(\d+) players online\. =============$" # Should return two match groups -- current players, max players.
    ),
    server_name = "Minecraft Server",
    latest_log_location = "/somewhere/latest.log", # Absolute path
    insertion_available = False, # If the server minecraft version supports `insertion` in tellraw commands.
)

echo = dict(
    bind = "tcp://*:9001",
    connect = "tcp://localhost:9001"
)

programs = dict(
    bridge = "webhook.py",
    echo = "echo.py",
    minecraft = "run.sh"
)

icons = dict(
    avatar_lookup_url = "https://crafatar.com/avatars/",
    uuid_lookup_url = "https://api.mojang.com/users/profiles/minecraft/",
    server = "http://media.fatboychummy.games/bots/mc_bridge/server_status.png",
    minecraft = "http://media.fatboychummy.games/bots/mc_bridge/minecraft_icon.png"
)