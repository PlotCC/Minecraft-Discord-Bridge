import datetime
import logging
try:
    from zoneinfo import ZoneInfo
except ImportError:
    try:
        from backports.zoneinfo import ZoneInfo
    except ImportError:
        raise ImportError("Both zoneinfo and backports.zoneinfo do not exist on this machine.")

bot = dict(
    # The channel that the bot should listen to. Slash-commands can occur
    # anywhere, but chatter in this channel will be the only one sent to the
    # server.
    channel_id = 0,

    # Your bot token. Take care not to commit this.
    token = "",

    # The prefix for jsk.
    prefix = ">> ",

    # The log level for the bot.
    logging_level = logging.INFO
)

server = dict(
    # Displayed as "Playing <name>" in the bot's status.
    name = "Minecraft Server",

    # Whether automatic restarts should occur or not.
    do_automatic_restart = True,

    # This is not the time the server restarts at, rather, it is the time that
    # the server restart delay begins. If the delay is 1 hour, the actual 
    # restart time is one hour in the future from this time.
    restart_time = datetime.time(hour=0, minute=0, second=0, tzinfo=ZoneInfo("America/Edmonton")),

    # The amount of time to warn players of a restart. Warnings occur every
    # hour, then at 30 mins, 15 mins, 10 mins, 5 mins, 1 min, 30 seconds, and
    # finally in a countdown from 10 seconds to 0.
    restart_delay = 3600, # 1 hour by default.
    root = "/somewhere/", # Absolute path to the minecraft server root folder

    # This section controls whether or not the bot pings you when the server crashes, and where/who it should ping.
    enable_notifications = True,
    notification_channel_id = 0,
    notification_role_id = 0,
    # If you want the bot to ping this role in the same message that it notifies the bridge channel of a crash, set this to True.
    # Otherwise, it will send a separate message to the notification channel.
    ping_role_in_bridge = False,
)

tmux_data = dict(
    # The tmux session name to use.
    tmux_session = "plotworld_server",

    # The name of the window in tmux.
    window_name ="console",
)

webhook = dict(
    # Your webhook url. Be careful not to commit this.
    url = "",

    # Regexes that the webhook checks for in the log file in order to send
    # messages to Discord.
    regex = dict(
        # Should return two match groups -- playername and message.
        player_message_noreply = "",

        # Should return four match groups -- message ID to reply to, 'pingon'/'pingoff', playername and message.
        # Do note, the server inserts automatically the phrase 'reply:ID:pingoff' or 'reply:ID:pingon' to the start of the message if insertion is enabled.
        player_message_reply = "",

        # Should return a single match group -- playername.
        player_joined = "",

        # Should return a single match group -- playername.
        player_left = "",

        # No groups required.
        server_starting = "",

        # No groups required.
        server_started = "",

        # No groups required.
        server_stopping = "",

        # Should return three match groups -- current players, max players, playerlist.
        server_list = "",

        # Should return a single match group -- message
        console_message = "",

        # Should return two match groups -- playername and advancement.
        advancement = "",
    ),

    # The webhook actions that are enabled and searched for in the logs.
    # If set to false, the event will not be sent to Discord.
    actions_enabled = dict(
        player_message_noreply = True,
        player_message_reply = True,
        player_joined = True,
        player_left = True,
        server_starting = True,
        server_started = True,
        server_stopping = True,
        server_list = True,
        console_message = True,
        advancement = True,
    ),

    # The name of the server, displayed when events like shutdowns or player joins occur.
    server_name = "Minecraft Server",

    # Absolute path to the latest log location.
    latest_log_location = "/somewhere/latest.log",

    # Set this to True if the minecraft version supports tellraw "insertion"
    # values. This allows players to click on discord usernames to reply to
    # them.
    insertion_available = False,
)

backups = dict(
    backup_location = "/somewhere/backups/", # Absolute path to the backups folder.
    world_location = "/somewhere/world/", # Absolute path to the world folder.

    # The amount of backups of each type to keep.
    hourly_backup_count = 12, # Keep x hours of backups.
    weekly_backup_count = 3, # If this is anything above 0, it will keep one daily backup from each week as a weekly backup, storing up to x weeks of backups.

    backup_name_format = "backup-{type}-{date}-{time}.zip",
)

programs = dict(
    # Minecraft program, this should start the minecraft server.
    minecraft = "./run.sh"
)

icons = dict(
    avatar_lookup_url = "https://crafatar.com/avatars/",
    uuid_lookup_url = "https://api.mojang.com/users/profiles/minecraft/",

    # Minecraft server icon. Currently not used.
    server = "http://media.fatboychummy.games/bots/mc_bridge/server_status.png",

    # Minecraft icon, displayed when the server changes states or players join/leave.
    minecraft = "http://media.fatboychummy.games/bots/mc_bridge/minecraft_icon.png",

    # Console icon, displayed when someone uses /say in the server console.
    console = "http://media.fatboychummy.games/bots/mc_bridge/terminal.png"
)