from enum import Enum

class FilterClassMood(int, Enum):
    NEGATIVE = 0
    POSITIVE = 1
    NEUTRAL = 2

    def __str__(self):
        return {
            self.NEGATIVE: "Негативный",
            self.POSITIVE: "Позитивный",
            self.NEUTRAL: "Нейтральный",
        }[self]