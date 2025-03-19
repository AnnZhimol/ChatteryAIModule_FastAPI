from enum import Enum

class FilterClassType(int, Enum):
    OPINION = 0
    QUESTION = 1
    APPEAL = 2

    def __str__(self):
        return {
            self.OPINION: "Повествование",
            self.QUESTION: "Вопрос",
            self.APPEAL: "Побуждение",
        }[self]