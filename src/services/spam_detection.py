import re
import string
import nltk
import os
from nltk.corpus import stopwords

nltk.download('stopwords')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "../utils", "russian_words.txt")

class SpamDetection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SpamDetection, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.russian_words = self.load_russian_words(FILE_PATH)
        self.russian_stopwords = set(stopwords.words('russian'))

    @staticmethod
    def load_russian_words(file_path):
        with open(file_path, encoding='windows-1251') as f:
            return set(f.read().splitlines())

    def is_russian_word(self, word):
        return word.isalpha() and word in self.russian_words and len(word) > 2

    def analyze_comment(self, comment: str) -> float:
        if not isinstance(comment, str) or not comment.strip():
            return 0

        comment = comment.strip()

        if all(c in string.punctuation for c in comment):
            return 100

        length = len(comment)
        words = re.findall(r'\b\w+\b', comment.lower())
        total_words = len(words)

        if total_words == 0:
            return 100

        unique_words = len(set(words))
        unique_chars = len(set(comment))

        word_repetition_ratio = total_words / unique_words if unique_words > 0 else 1
        char_repetition_ratio = length / unique_chars if unique_chars > 0 else 1
        links_count = len(re.findall(r'(https?://|www\.|\.com|\.ru|\.net|\.org)', comment))

        uppercase_count = sum(1 for c in comment if c.isupper())
        caps_percentage = uppercase_count / length if length > 0 else 0

        special_chars_count = sum(1 for c in comment if c in string.punctuation)
        special_chars_percentage = special_chars_count / length if length > 0 else 0

        short_words = sum(1 for word in words if len(word) <= 3)
        short_word_ratio = short_words / total_words if total_words > 3 else 0

        monotony_score = sum(len(match.group()) for match in re.finditer(r'(.)\1{2,}', comment)) / length if length > 10 else 0
        nonsense_words = sum(1 for word in words if not self.is_russian_word(word))
        nonsense_ratio = nonsense_words / total_words if total_words > 0 else 0

        stopwords_count = sum(1 for word in words if word in self.russian_stopwords)
        stopwords_ratio = stopwords_count / total_words if total_words > 0 else 0

        short_comment_penalty = 5 if total_words <= 2 else 0

        alpha, beta, gamma, delta, epsilon = 2.0, 1.2, 2.0, 1.8, 4.5
        zeta, eta, theta, stopword_penalty = 1.0, 2.2, 1.5, 2.5

        spam_score = (
            alpha * word_repetition_ratio +
            beta * char_repetition_ratio +
            gamma * caps_percentage +
            delta * special_chars_percentage +
            epsilon * links_count +
            zeta * short_word_ratio +
            eta * monotony_score +
            theta * nonsense_ratio +
            short_comment_penalty -
            stopword_penalty * stopwords_ratio
        )

        spam_probability = min(100, max(0, round(spam_score * 10)))

        if total_words > 15 and links_count == 0 and monotony_score < 0.05 and nonsense_ratio < 0.2:
            spam_probability *= 0.4

        return round(spam_probability, 2)