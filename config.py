bot = dict(
    channel_id = 0,
    token = ""
)

webhook = dict(
    url = "",
    regex = dict(
        player_message = "^\[\d\d:\d\d:\d\d] \[Server thread/INFO\] \[net\.minecraft\.server\.dedicated\.DedicatedServer\]: \[.*?\] (.*?): (.+)$", # Should return two match groups -- playername and message.
        player_joined = "^\[\d\d:\d\d:\d\d\] \[Server thread/INFO\] \[net\.minecraft\.server\.dedicated\.DedicatedServer\]: (.*?) joined the game$", # Should return a single match group -- playername.
        player_left = "^\[\d\d:\d\d:\d\d\] \[Server thread/INFO\] \[net\.minecraft\.server\.dedicated\.DedicatedServer\]: (.*?) left the game$" # Should return a single match group -- playername.
    ),
    server_name = "Minecraft Server",
    latest_log_location = "latest.log"
)

icons = dict(
    avatar_lookup_url = "https://crafatar.com/avatars/",
    uuid_lookup_url = "https://api.mojang.com/users/profiles/minecraft/",
    server = "https://fatboychummy.games/static/bots/mc_bridge/server_status.png",
    minecraft = "https://fatboychummy.games/static/bots/mc_bridge/minecraft_icon.png"
)