import string

import nltk
import spacy
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from tensorflow.keras.preprocessing.sequence import pad_sequences
import tensorflow as tf
import pickle
import os

from src.enums.filter_class_mood import FilterClassMood

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "utils", "best_model_lstm_sentiment_83.h5")
TOKENIZER_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "utils", "tokenizer_sentiment.pkl"))
nltk.download('punkt_tab')

class ModelLoaderSentiment:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoaderSentiment, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.nlp = spacy.load("ru_core_news_sm")
        self.model = tf.keras.models.load_model(MODEL_PATH,compile=False)
        with open(TOKENIZER_PATH, 'rb') as handle:
            self.tokenizer = pickle.load(handle)
        self.stop_words = set(stopwords.words('russian'))
        self.punctuation = set(string.punctuation)

    def process_text(self, message_text: str) -> FilterClassMood:
        max_reviews_len = 20
        filtered_tokens = []

        words = word_tokenize(message_text)
        filtered_words = [word for word in words if word.lower() and word != "''" and word != '«' and word != '»'
                          and word not in self.stop_words and word not in self.punctuation]
        filtered_tokens.extend(filtered_words)

        lemmatized_words = [token.lemma_ for token in self.nlp(" ".join(filtered_tokens))]

        sequence = self.tokenizer.texts_to_sequences([lemmatized_words])
        data = pad_sequences(sequence, maxlen=max_reviews_len)

        result_lstm = self.model.predict(data)

        if 0.3 < result_lstm[[0]] < 0.6:
            return FilterClassMood.NEUTRAL
        if result_lstm[[0]] >= 0.6:
            return FilterClassMood.POSITIVE
        if result_lstm[[0]] <= 0.3:
            return FilterClassMood.NEGATIVE


class PredictSentiment:
    def __init__(self):
        self.model_loader = ModelLoaderSentiment()

    def get_class(self, message_text: str) -> FilterClassMood:
        return self.model_loader.process_text(message_text)