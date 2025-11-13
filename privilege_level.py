from enum import Enum

class PrivilegeLevel(Enum):
    BANNED = 0
    USER = 1
    MODERATOR = 2
    ADMIN = 3
    OWNER = 4

    # Comparison operators for privilege levels.
    def __lt__(self, other):
        if isinstance(other, PrivilegeLevel):
            return self.value < other.value
        elif isinstance(other, int):
            return self.value < other
        return NotImplemented
    
    def __le__(self, other):
        if isinstance(other, PrivilegeLevel):
            return self.value <= other.value
        elif isinstance(other, int):
            return self.value <= other
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, PrivilegeLevel):
            return self.value > other.value
        elif isinstance(other, int):
            return self.value > other
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, PrivilegeLevel):
            return self.value >= other.value
        elif isinstance(other, int):
            return self.value >= other
        return NotImplemented