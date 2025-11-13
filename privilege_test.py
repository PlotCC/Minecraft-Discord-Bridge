import discord
from config import privileges
from privilege_level import PrivilegeLevel



def test(interaction: discord.Interaction|discord.Message, level: PrivilegeLevel) -> bool:
    """
    Check if the user has the required privilege level.
    """
    user_id = interaction.user.id if isinstance(interaction, discord.Interaction) else interaction.author.id
    user_level = privileges.users.get(user_id, privileges.user)
    return user_level >= level



def reject_message(level: PrivilegeLevel) -> str:
    """
    Get the rejection message for a user without sufficient privileges.
    """
    return f"You do not have permission to use this command (requires {level.name.title()})."