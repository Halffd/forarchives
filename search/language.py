import logging
from nltk.stem import WordNetLemmatizer
from nltk.stem import SnowballStemmer
import MeCab

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LanguageProcessor:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stemmers = {
            'es': SnowballStemmer('spanish'),  # Spanish
            'pt': SnowballStemmer('portuguese'),  # Portuguese
            'de': SnowballStemmer('german'),  # German
            'fr': SnowballStemmer('french'),  # French
            'it': SnowballStemmer('italian'),  # Italian
            'ja': MeCab.Tagger('-Owakati')  # Japanese MeCab Tagger
        }

    def unconjugate_word(self, word: str, language: str = 'en', toggle: bool = True) -> str:
        """
        Unconjugate a given word based on its language.

        Parameters:
        - word (str): The word to be unconjugated.
        - language (str): The language of the word. Defaults to 'en' for English.
        - toggle (bool): If True, perform unconjugation. If False, return the original word.

        Returns:
        - str: The unconjugated form of the word, or the original if toggle is False.
        """
        if not toggle:
            logger.info("Toggle is False, returning original word.")
            return word

        logger.info(f"Unconjugating word: {word} in language: {language}")

        if language == 'en':
            unconjugated_word = self.lemmatizer.lemmatize(word)
            logger.debug(f"Unconjugated word (English): {unconjugated_word}")
            return unconjugated_word
        elif language in self.stemmers:
            stemmer = self.stemmers[language]
            if language == 'ja':
                unconjugated_word = self.unconjugate_japanese(word)
                logger.debug(f"Unconjugated word (Japanese): {unconjugated_word}")
                return unconjugated_word
            elif stemmer:
                unconjugated_word = stemmer.stem(word)
                logger.debug(f"Unconjugated word ({language}): {unconjugated_word}")
                return unconjugated_word
        else:
            logger.warning(f"Unsupported language: {language}. Returning original word.")
            return word

    def unconjugate_japanese(self, word: str) -> str:
        """
        Unconjugate a Japanese word using MeCab.

        Parameters:
        - word (str): The Japanese word to be unconjugated.

        Returns:
        - str: The unconjugated form of the Japanese word.
        """
        # Use MeCab to tokenize the word
        parsed = self.stemmers['ja'].parse(word)
        # Extract the base form (the first token usually represents the root form)
        base_form = parsed.split()[0].split('/')[0]  # Get the first part before the '/'
        return base_form

    def unconjugate_words(self, words: list, language: str = 'en', toggle: bool = True) -> list:
        """
        Unconjugate a list of words based on their language.

        Parameters:
        - words (list): A list of words to be unconjugated.
        - language (str): The language of the words. Defaults to 'en' for English.
        - toggle (bool): If True, perform unconjugation. If False, return the original words.

        Returns:
        - list: A list of unconjugated words, or the original list if toggle is False.
        """
        if not toggle:
            logger.info("Toggle is False, returning original list of words.")
            return words

        logger.info(f"Unconjugating list of words in language: {language}")
        unconjugated_words = [self.unconjugate_word(word, language) for word in words]
        logger.debug(f"Unconjugated words: {unconjugated_words}")
        return unconjugated_words