import datetime
import logging
from zoneinfo import ZoneInfo
from privelege_level import PrivelegeLevel
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Bot:
    # The channel that the bot should listen to. Slash-commands can occur
    # anywhere, but chatter in this channel will be the only one sent to the
    # server.
    channel_id: int = 0

    # Your bot token. Take care not to commit this.
    token: str = ""

    # The prefix for jsk.
    prefix: str = ">> "

    # The log level for the bot.
    logging_level: int = logging.INFO

    # The bot's owner's user ID.
    owner_id: int = 0
bot = Bot()



@dataclass(frozen=True)
class Priveleges:
    # The levels of priveleges for various roles.
    banned: PrivelegeLevel = PrivelegeLevel.BANNED
    user: PrivelegeLevel = PrivelegeLevel.USER
    moderator: PrivelegeLevel = PrivelegeLevel.MODERATOR
    admin: PrivelegeLevel = PrivelegeLevel.ADMIN
    owner: PrivelegeLevel = PrivelegeLevel.OWNER

    # The privelege required to use rcon commands.
    rcon_command_privelege: PrivelegeLevel = PrivelegeLevel.ADMIN

    # The privelege required to use meta rcon commands.
    rcon_meta_command_privelege: PrivelegeLevel = PrivelegeLevel.ADMIN

    # The privelege required to send commands to the server console
    console_command_privelege: PrivelegeLevel = PrivelegeLevel.ADMIN

    # The privelege required to start/stop/restart the server.
    server_control_privelege: PrivelegeLevel = PrivelegeLevel.MODERATOR

    # The privelege required to view/create backups.
    backup_privelege: PrivelegeLevel = PrivelegeLevel.MODERATOR

    # Map of user IDs to their privelege levels.
    users: dict[int, PrivelegeLevel] = field(
        default_factory=lambda: {
            bot.owner_id: PrivelegeLevel.OWNER
        }
    )
priveleges = Priveleges()



@dataclass(frozen=True)
class Server:
    # Displayed as "Playing <name>" in the bot's status.
    name: str = "Minecraft Server"

    # Whether automatic restarts should occur or not.
    do_automatic_restart: bool = True

    # This is not the time the server restarts at, rather, it is the time that
    # the server restart delay begins. If the delay is 1 hour, the actual 
    # restart time is one hour in the future from this time.
    restart_time: datetime.time = datetime.time(hour=0, minute=0, second=0, tzinfo=ZoneInfo("America/Edmonton"))

    # The amount of time to warn players of a restart. Warnings occur every
    # hour, then at 30 mins, 15 mins, 10 mins, 5 mins, 1 min, 30 seconds, and
    # finally in a countdown from 10 seconds to 0.
    restart_delay: int = 3600  # 1 hour by default.
    root: str = "/somewhere/"  # Absolute path to the minecraft server root folder
    
    # This section controls whether or not the bot pings you when the server crashes, and where/who it should ping.
    enable_notifications: bool = True
    notification_channel_id: int = 0
    notification_role_id: int = 0
    # If you want the bot to ping this role in the same message that it notifies the bridge channel of a crash, set this to True.
    # Otherwise, it will send a separate message to the notification channel.
    ping_role_in_bridge: bool = False
server = Server()



@dataclass(frozen=True)
class Rcon:
    # rcon password for the server.
    password: str = "password"

    # rcon IP address
    host: str = "127.0.0.1"

    # rcon port
    port: int = 25575

    # Channel ID for rcon.
    channel_id: int = 0

    # The prefix to use for rcon commands.
    command_prefix: str = "!"

    # The prefix to use for meta rcon commands (reconnect, status, etc.).
    meta_command_prefix: str = ";"
rcon = Rcon()



@dataclass(frozen=True)
class TmuxData:
    # The tmux session name to use.
    tmux_session: str = "plotworld_server"

    # The name of the window in tmux.
    window_name: str = "console"
tmux_data = TmuxData()



@dataclass(frozen=True)
class Webhook:
    # Your webhook url. Be careful not to commit this.
    url: str = ""

    # Regexes that the webhook checks for in the log file in order to send
    # messages to Discord.
    regex: dict[str, str] = field(
        default_factory=lambda: {
            # Should return two match groups -- playername and message.
            "player_message_noreply": "",

            # Should return four match groups -- message ID to reply to, 'pingon'/'pingoff', playername and message.
            # Do note, the server inserts automatically the phrase 'reply:ID:pingoff' or 'reply:ID:pingon' to the start of the message if insertion is enabled.
            "player_message_reply": "",

            # Should return a single match group -- playername.
            "player_joined": "",

            # Should return a single match group -- playername.
            "player_left": "",

            # No groups required.
            "server_starting": "",

            # No groups required.
            "server_started": "",

            # No groups required.
            "server_stopping": "",

            # Should return three match groups -- current players, max players, playerlist.
            "server_list": "",

            # Should return a single match group -- message
            "console_message": "",

            # Should return two match groups -- playername and advancement.
            "advancement": "",

            # Player attempted to join and is not whitelisted -- playername.
            "not_whitelisted": "",
        }
    )

    # The webhook actions that are enabled and searched for in the logs.
    # If set to false, the event will not be sent to Discord.
    actions_enabled: dict[str, bool] = field(
        default_factory=lambda: {
            "player_message_noreply": True,
            "player_message_reply": True,
            "player_joined": True,
            "player_left": True,
            "server_starting": True,
            "server_started": True,
            "server_stopping": True,
            "server_list": True,
            "console_message": True,
            "advancement": True,
            "not_whitelisted": True,
        }
    )

    # The name of the server, displayed when events like shutdowns or player joins occur.
    server_name: str = "Minecraft Server"

    # Absolute path to the latest log location.
    latest_log_location: str = "/somewhere/latest.log"

    # Set this to True if the minecraft version supports tellraw "insertion"
    # values. This allows players to click on discord usernames to reply to
    # them.
    insertion_available: bool = False
webhook = Webhook()



@dataclass(frozen=True)
class Backups:
    # Absolute path to the backups folder.
    backup_location: str = "/somewhere/backups/"

    # Absolute path to the world folder.
    world_location: str = "/somewhere/world/"

    # The amount of backups of each type to keep.
    hourly_backup_count: int = 12  # Keep x hours of backups.
    daily_backup_count: int = 6  # Keep x days of backups.
    weekly_backup_count: int = 3  # If this is anything above 0, it will keep one daily backup from each week as a weekly backup, storing up to x weeks of backups.
backups = Backups()



@dataclass(frozen=True)
class Console:
    # Minecraft run command, this should start the minecraft server.
    minecraft: str = "./run.sh"
console = Console()



@dataclass(frozen=True)
class Icons:
    # URLs for various icons used by the bot.
    avatar_lookup_url: str = "https://crafatar.com/avatars/"
    uuid_lookup_url: str = "https://api.mojang.com/users/profiles/minecraft/"

    # Minecraft server icon. Currently not used.
    server: str = "http://media.fatboychummy.games/bots/mc_bridge/server_status.png"

    # Minecraft icon, displayed when the server changes states or players join/leave.
    minecraft: str = "http://media.fatboychummy.games/bots/mc_bridge/minecraft_icon.png"

    # Console icon, displayed when someone uses /say in the server console.
    console: str = "http://media.fatboychummy.games/bots/mc_bridge/terminal.png"
icons = Icons()