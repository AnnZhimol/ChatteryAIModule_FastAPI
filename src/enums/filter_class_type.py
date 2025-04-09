from enum import Enum

class FilterClassType(int, Enum):
    OPINION = 0
    QUESTION = 1
    APPEAL = 2

    def __str__(self):
        return {
            self.OPINION: "OPINION",
            self.QUESTION: "QUESTION",
            self.APPEAL: "APPEAL",
        }[self]