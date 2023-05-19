bot = dict(
    channel_id = 0,
    token = "",
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
    ),
    server_name = "Minecraft Server",
    latest_log_location = "/somewhere/latest.log" # Absolute path
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
    server = "https://fatboychummy.games/static/bots/mc_bridge/server_status.png",
    minecraft = "https://fatboychummy.games/static/bots/mc_bridge/minecraft_icon.png"
)