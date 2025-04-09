from enum import Enum

class FilterClassMood(int, Enum):
    NEGATIVE = 0
    POSITIVE = 1
    NEUTRAL = 2

    def __str__(self):
        return {
            self.NEGATIVE: "NEGATIVE",
            self.POSITIVE: "POSITIVE",
            self.NEUTRAL: "NEUTRAL",
        }[self]