import os
import re
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import os
import sys

class Utilities:
    def __init__(self, log_dir="logs"):
        self.log_dirname = log_dir
        base = os.path.dirname(sys.argv[0])
        self.log_dir = os.path.join(base, self.log_dirname)
        self.create_log_directory()
        self.print = print
    def create_log_directory(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    def printLog(self, *message, sep=' ', end='\n', file=None, flush=False, **kwargs):
        """
        Custom print function that logs messages and optionally prints to console.

        This function is a near-drop-in replacement for the built-in `print` function.
        It provides logging functionality and allows for custom arguments similar to `print`.

        Args:
            *message: The message to be printed and logged.
            sep: Separator between messages. Defaults to ' '.
            end: Character(s) to be printed at the end of the output. Defaults to '\n'.
            file: A file-like object (stream) to write the output to. Defaults to sys.stdout.
            flush: If True, the stream is flushed after writing. Defaults to False.
            **kwargs: Additional keyword arguments.
            - 'file': Filename for logging. If not specified, defaults to None (no logging).
        """
        # Extract optional arguments from kwargs
        log_file = kwargs.pop('file', 'output')  # Use None if not provided
        print_to_console = kwargs.pop('print', True)
         # Logging setup if a log file is provided
        if log_file:
            log_file = self.clean_filename(log_file)
            log_file = self.get_log_file(log_file)
            logging.basicConfig(filename=log_file, level=logging.INFO, encoding='utf-8',
                                format='%(asctime)s - %(levelname)s - %(message)s')
            logging.info(*message)

        # Print to console if print=True
        if print_to_console:
            self.print(*message, sep=sep, end=end, file=file, flush=flush) 
    def log(self, message, board = '', query = '', site = ''):
        query = self.clean_filename(query)
        log_file = self.get_log_file(site, board, query)
        logging.basicConfig(filename=log_file, level=logging.INFO, encoding='utf-8',
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info(message)
    def clean_filename(self, filename):
        # Remove leading/trailing spaces
        filename = filename.strip()
        
        # Remove leading/trailing periods
        filename = filename.strip('.')
        
        # Replace multiple consecutive periods with a single period
        filename = re.sub(r'\.+', '.', filename)
            
        # Remove other special characters
        cleaned_filename = re.sub(r"[<>!@#$%^&*(),/'?\|\"\-;:\[\]\{\}|\\]", "", filename)
        if cleaned_filename[-1] == ".":
            cleaned_filename = cleaned_filename[:-1]
        return cleaned_filename
    def get_log_file(self, site, board = '', query = ''):
        today = datetime.now()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")
        log_file_path = os.path.join(self.log_dir, year, month, day)

        # Create directories if they do not exist
        os.makedirs(log_file_path, exist_ok=True)

        # Create the log file with the specified naming convention
        params= []
        if site:
            params.append(site)
        if board:
            params.append(board)
        if query:
            params.append(query)

        # Join the parameters with hyphens
        params_str = '-'.join(params)

        # Create the full log file name
        log_file_name = f"{today.strftime('%Y-%m-%d')}-{params_str}.log" if params_str else f"{today.strftime('%Y-%m-%d')}.log"

        return os.path.join(log_file_path, log_file_name)
    def key_by_value(self, d, value):
        """
        Retrieve the key from a dictionary by its value.

        Parameters:
        d (dict): The dictionary to search.
        value: The value to find the corresponding key for.

        Returns:
        The key corresponding to the value, or None if not found.
        """
        return next((k for k, v in d.items() if v == value), None)
    def parse_search_terms(self, search_terms):
        terms = search_terms.split()
        regex_parts = []

        for term in terms:
            if term.startswith('-'):  # Negation
                negated_term = re.escape(term[1:])
                regex_parts.append(f"(?!.*{negated_term})")  # Exclude this term
            elif '&' in term:  # AND operator
                and_terms = term.split('&')
                and_part = ''.join(f"(?=.*{re.escape(t.strip())})" for t in and_terms)
                regex_parts.append(f"({and_part})")
            elif '|' in term:  # OR operator
                or_terms = term.split('|')
                or_part = '|'.join(f".*{re.escape(t.strip())}.*" for t in or_terms)
                regex_parts.append(f"({or_part})")
            elif '"' in term:  # Exact phrase
                phrase = term.strip('"')
                regex_parts.append(f".*\\b{re.escape(phrase)}\\b.*")  # Use word boundaries for exact match
            else:  # Regular term or wildcard
                if '*' in term or '?' in term:
                    term = re.escape(term).replace(r'\*', '.*').replace(r'\?', '.')
                regex_parts.append(f".*{term}.*")  # Match any part of the string

        combined_regex = ''.join(regex_parts)
        return combined_regex

    def is_regex(self, term):
        regex_metacharacters = r'[\.\*\?\(\)[]\\\+\^\$\{\}]'
        return bool(re.search(regex_metacharacters, term))

    def regex_search(self, array, search_terms, case_sensitive=False):
        is_regex = self.is_regex(search_terms)
        if is_regex:
            pattern = search_terms  # Use as-is if it's regex
        else:
            pattern = self.parse_search_terms(search_terms)

        regex_flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, regex_flags)
        found_items = [item for item in array if regex.search(item)]

        if any(term.startswith('-') for term in search_terms.split()):
            for term in search_terms.split():
                if term.startswith('-'):
                    negated_term = re.escape(term[1:])
                    found_items = [item for item in found_items if not re.search(negated_term, item)]

        return found_items

    def plot_statistics(self, post_dates):
        if not post_dates:
            print("No data to plot.")
            return

        # Count posts per day
        date_counts = {}
        for date in post_dates:
            date_str = date.date().isoformat()
            if date_str in date_counts:
                date_counts[date_str] += 1
            else:
                date_counts[date_str] = 1

        # Prepare data for plotting
        dates = list(date_counts.keys())
        counts = list(date_counts.values())

        plt.figure(figsize=(10, 5))
        plt.bar(dates, counts, color='blue')
        plt.xlabel('Date')
        plt.ylabel('Number of Posts')
        plt.title('Posts Distribution Over Dates')
        plt.xticks(rotation=45)
        plt.tight_layout()  # Adjust layout to prevent overlap
        plt.show()