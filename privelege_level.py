from enum import Enum
import discord
from config import priveleges

class PrivelegeLevel(Enum):
    BANNED = 0
    USER = 1
    MODERATOR = 2
    ADMIN = 3
    OWNER = 4

    # Comparison operators for privelege levels.
    def __lt__(self, other):
        if isinstance(other, PrivelegeLevel):
            return self.value < other.value
        elif isinstance(other, int):
            return self.value < other
        return NotImplemented
    
    def __le__(self, other):
        if isinstance(other, PrivelegeLevel):
            return self.value <= other.value
        elif isinstance(other, int):
            return self.value <= other
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, PrivelegeLevel):
            return self.value > other.value
        elif isinstance(other, int):
            return self.value > other
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, PrivelegeLevel):
            return self.value >= other.value
        elif isinstance(other, int):
            return self.value >= other
        return NotImplemented



def test(interaction: discord.Interaction|discord.Message, level: PrivelegeLevel) -> bool:
    """
    Check if the user has the required privelege level.
    """
    user_id = interaction.user.id if isinstance(interaction, discord.Interaction) else interaction.author.id
    user_level = priveleges.users.get(user_id, priveleges.user)
    return user_level >= level