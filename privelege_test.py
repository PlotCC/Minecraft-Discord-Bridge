import discord
from config import priveleges
from privelege_level import PrivelegeLevel



def test(interaction: discord.Interaction|discord.Message, level: PrivelegeLevel) -> bool:
    """
    Check if the user has the required privelege level.
    """
    user_id = interaction.user.id if isinstance(interaction, discord.Interaction) else interaction.author.id
    user_level = priveleges.users.get(user_id, priveleges.user)
    return user_level >= level



def reject_message(level: PrivelegeLevel) -> str:
    """
    Get the rejection message for a user without sufficient priveleges.
    """
    return f"You do not have permission to use this command (requires {level.name.title()})."