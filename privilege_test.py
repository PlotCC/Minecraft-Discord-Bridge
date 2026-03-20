import discord
from discord import app_commands
from config import privileges
from privilege_level import PrivilegeLevel


class InsufficientPrivilegeException(Exception):
    pass



def reject_message(level: PrivilegeLevel) -> str:
    """
    Get the rejection message for a user without sufficient privileges.
    """
    return f"You do not have permission to use this command (requires {level.name.title()})."



async def test(interaction: discord.Interaction|discord.Message, level: PrivilegeLevel) -> bool:
    """
    Check if the user has the required privilege level.
    """
    user_id = interaction.user.id if isinstance(interaction, discord.Interaction) else interaction.author.id
    user_level = privileges.users.get(user_id, privileges.user)
    if user_level < level and isinstance(interaction, discord.Interaction):
        await interaction.response.send_message(reject_message(level))
        raise InsufficientPrivilegeException(reject_message(level))
    return user_level >= level


def check_permissions(level: PrivilegeLevel):
    def predicate(interaction: discord.Interaction) -> bool:
        user_id = interaction.user.id
        user_level = privileges.users.get(user_id, privileges.user)
        if user_level < level:
            raise InsufficientPrivilegeException(reject_message(level))
        return True
    return app_commands.check(predicate)