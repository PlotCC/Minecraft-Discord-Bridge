from enum import Enum

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