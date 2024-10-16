import logging
import re
from language import LanguageProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchEngine:
    def __init__(self):
        self.language_processor = LanguageProcessor()

    def parse_search_terms(self, search_terms, whole_word=False):
        terms = search_terms.split()
        regex_parts = []

        for term in terms:
            if term.startswith('-'):
                negated_term = re.escape(term[1:])
                regex_parts.append(f"(?!\\b{negated_term}\\b)" if whole_word else f"(?!.*{negated_term})")
            elif '&' in term:
                and_terms = term.split('&')
                and_part = ''.join(f"(?=.*\\b{re.escape(t.strip())}\\b)" if whole_word else f"(?=.*{re.escape(t.strip())})" for t in and_terms)
                regex_parts.append(f"({and_part})")
            elif '|' in term:
                or_terms = term.split('|')
                or_part = '|'.join(f"(.*\\b{re.escape(t.strip())}\\b.*)" if whole_word else f"(.*{re.escape(t.strip())}.*)" for t in or_terms)
                regex_parts.append(f"({or_part})")
            elif '"' in term:
                phrase = term.strip('"')
                regex_parts.append(f".*\\b{re.escape(phrase)}\\b.*" if whole_word else f".*{re.escape(phrase)}.*")
            else:
                term_pattern = re.escape(term).replace(r'\*', '.*').replace(r'\?', '.')
                regex_parts.append(f".*\\b{term_pattern}\\b.*" if whole_word else f".*{term_pattern}.*")

        return ''.join(regex_parts)

    def regex_search(self, array, search_terms, case_sensitive=False, whole_word=False, toggle_unconjugate=False, language='en', isRegex=0):
        """
        Search for items in the array based on search terms.

        Parameters:
        - array (list): The list of items to search.
        - search_terms (str): The search terms.
        - case_sensitive (bool): Whether the search should be case-sensitive.
        - whole_word (bool): Whether to match whole words only.
        - toggle_unconjugate (bool): Whether to unconjugate search terms.
        - language (str): Language for unconjugation if applicable.
        - isRegex (int): 0 for no detection, 1 for regex detection, 2 for string search.

        Returns:
        - list: The list of found items.
        """
        # Unconjugate search terms if the toggle is set
        if toggle_unconjugate:
            search_terms = ' '.join(
                self.language_processor.unconjugate_word(term, language, toggle=True)
                for term in search_terms.split()
            )

        # Determine search type based on isRegex parameter
        if isRegex == 0:
            # No regex detection or usage
            pattern = re.escape(search_terms)
            regex = re.compile(pattern, re.IGNORECASE if not case_sensitive else 0)
            found_items = [item for item in array if regex.search(item)]
        elif isRegex == 1:
            # Use search terms as regex
            pattern = self.parse_search_terms(search_terms, whole_word)
            regex_flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, regex_flags)
            found_items = [item for item in array if regex.search(item)]
        elif isRegex == 2:
            # String search without regex
            found_items = [item for item in array if search_terms in item]

        # Handle negation after the main search
        for term in search_terms.split():
            if term.startswith('-'):
                negated_term = re.escape(term[1:])
                found_items = [item for item in found_items if not re.search(negated_term, item)]

        return found_items
gine, language unconjugator

Copy
import logging
from nltk.stem import WordNetLemmatizer
from nltk.stem import SnowballStemmer
import MeCab
import re

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
        if not toggle:
            return word

        if language == 'en':
            return self.lemmatizer.lemmatize(word)
        elif language in self.stemmers:
            stemmer = self.stemmers[language]
            if language == 'ja':
                return self.unconjugate_japanese(word)
            elif stemmer:
                return stemmer.stem(word)
        return word

    def unconjugate_japanese(self, word: str) -> str:
        parsed = self.stemmers['ja'].parse(word)
        base_form = parsed.split()[0].split('/')[0]
        return base_form

class SearchEngine:
    def __init__(self):
        self.language_processor = LanguageProcessor()

    def parse_search_terms(self, search_terms, whole_word=False):
        terms = search_terms.split()
        regex_parts = []

        for term in terms:
            if term.startswith('-'):
                negated_term = re.escape(term[1:])
                regex_parts.append(f"(?!\\b{negated_term}\\b)" if whole_word else f"(?!.*{negated_term})")
            elif '&' in term:
                and_terms = term.split('&')
                and_part = ''.join(f"(?=.*\\b{re.escape(t.strip())}\\b)" if whole_word else f"(?=.*{re.escape(t.strip())})" for t in and_terms)
                regex_parts.append(f"({and_part})")
            elif '|' in term:
                or_terms = term.split('|')
                or_part = '|'.join(f"(.*\\b{re.escape(t.strip())}\\b.*)" if whole_word else f"(.*{re.escape(t.strip())}.*)" for t in or_terms)
                regex_parts.append(f"({or_part})")
            elif '"' in term:
                phrase = term.strip('"')
                regex_parts.append(f".*\\b{re.escape(phrase)}\\b.*" if whole_word else f".*{re.escape(phrase)}.*")
            else:
                term_pattern = re.escape(term).replace(r'\*', '.*').replace(r'\?', '.')
                regex_parts.append(f".*\\b{term_pattern}\\b.*" if whole_word else f".*{term_pattern}.*")

        return ''.join(regex_parts)

    def regex_search(self, array, search_terms, case_sensitive=False, whole_word=False, toggle_unconjugate=False, language='en', isRegex=0):
        """
        Search for items in the array based on search terms.

        Parameters:
        - array (list): The list of items to search.
        - search_terms (str): The search terms.
        - case_sensitive (bool): Whether the search should be case-sensitive.
        - whole_word (bool): Whether to match whole words only.
        - toggle_unconjugate (bool): Whether to unconjugate search terms.
        - language (str): Language for unconjugation if applicable.
        - isRegex (int): 0 for no detection, 1 for regex detection, 2 for string search.

        Returns:
        - list: The list of found items.
        """
        if toggle_unconjugate:
            search_terms = ' '.join(
                self.language_processor.unconjugate_word(term, language, toggle=True)
                for term in search_terms.split()
            )

        # Determine search type based on isRegex parameter
        if isRegex == 0:
            pattern = re.escape(search_terms)
            regex = re.compile(pattern, re.IGNORECASE if not case_sensitive else 0)
            found_items = [item for item in array if regex.search(item)]
        elif isRegex == 1:
            pattern = self.parse_search_terms(search_terms, whole_word)
            regex_flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, regex_flags)
            found_items = [item for item in array if regex.search(item)]
        elif isRegex == 2:
            found_items = [item for item in array if search_terms in item]

        # Handle negation after the main search
        for term in search_terms.split():
            if term.startswith('-'):
                negated_term = re.escape(term[1:])
                found_items = [item for item in found_items if not re.search(negated_term, item)]

        return found_items

if __name__ == "__main__":
    import sys

    # Read input from command line
    if len(sys.argv) < 4:
        print("Usage: python script.py <array_items_separated_by_>_<search_terms_separated_by_> <toggle_unconjugate> <isRegex>")
        sys.exit(1)

    # Parse command line arguments
    array_input = sys.argv[1].split('_')
    search_input = sys.argv[2].split('_')
    toggle_unconjugate = bool(int(sys.argv[3]))
    isRegex = int(sys.argv[4]) if len(sys.argv) > 4 else 0  # Default to 0 if not provided

    # Initialize search engine
    search_engine = SearchEngine()

    # Perform searches
    for search_term in search_input:
        results = search_engine.regex_search(
            array=array_input,
            search_terms=search_term,
            case_sensitive=False,
            toggle_unconjugate=toggle_unconjugate,
            language='en',  # Default language
            isRegex=isRegex
        )
        print(f"Search results for '{search_term}': {results}")