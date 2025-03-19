import random

class GenerateCred:
    def __init__(self, prefix="justinfan"):
        self.prefix = prefix

    def generate(self):
        suffix_length = random.randint(4, 5)
        suffix = "".join(str(random.randint(0, 9)) for _ in range(suffix_length))
        return f"{self.prefix}{suffix}"