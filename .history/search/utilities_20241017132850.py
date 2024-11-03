import os
import re
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import os
import sys
import json

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
            self.log(message, query=log_file,folderName='print',include_date=True,level='INFO')
        # Print to console if print=True
        if print_to_console:
            self.print(*message, sep=sep, end=end, file=file, flush=flush) 
    def log(self, message, board='', query='', site='', folderName = '', mode='a', encoding='utf-8', include_date=False, level='', isJson=False):
        query = self.clean_filename(query)
        log_file = self.get_log_file(site, board, query, folderName)
        
        # Prepare the log entry
        log_entry = self.format_log_entry(message, level, include_date)
        
        # Write to the log file
        with open(log_file, mode=mode, encoding=encoding) as f:
            f.write(log_entry + '\n')
    
        if isJson:
            self.json(*message,board=board,query=query,folderName=folderName, mode=mode, encoding=encoding, include_date=include_date, level=level)
    def json(self, data='', board='', query='', site='', folderName='', mode='a', encoding='utf-8', include_date=False, level=''):
        queryN = self.clean_filename(query)
        log_file = self.get_log_file(site, board, 'json/' + queryN, folderName)

        # Create a JSON object for the log entry
        log_data = {
            "data": data,
            "board": board,
            "query": query,
            "site": site,
            "folderName": folderName,
            "level": level,
            "timestamp": datetime.now().isoformat() if include_date else None
        }
        # Write to the log file as JSON
        with open(log_file, mode=mode, encoding=encoding) as f:
            json.dump(log_data, f)
            f.write('\n')  # Ensure each log entry is on a new line
    def format_log_entry(self, message, level='INFO', include_date=True):
        # Get the current timestamp if include_date is True
        timestamp = datetime.now().strftime('%Y-%m-%d') if include_date else ''
        date_part = f"{timestamp} - " if include_date else ''
        if level:
            level  += ' - '
        return f"{date_part}{level}{message}"
    def clean_filename(self, filename):
        # Remove leading/trailing spaces
        if not filename:
            return '0'
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
    def get_log_file(self, site, board = '', query = '', folderName = '', fileType=''):
        today = datetime.now()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")
        jsonF = 'json/' in query
        if jsonF:
            query = query.replace('json/','')
        path = [self.log_dir, f'{year}-{month}', day] if not jsonF else [self.log_dir, 'json']
        path.append(folderName)
        log_file_path = os.path.join(*path)

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
        # Get the current date and time
        now = datetime.now()
        # Format the string
        formatted_string = now.strftime('%Y-%d-%m')
        # Create the full log file name
        if fileType == '':
            fileType = 'json' if jsonF else 'log'
        log_file_name = f"{formatted_string}-{params_str}.{fileType}" if params_str else f"{formatted_string}.{fileType}"

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
    def df_get(self, df, row_index, column_name):
        """
        Get a value from a DataFrame.

        Parameters:
        df (pd.DataFrame): The DataFrame to search.
        row_index (int): The index of the row.
        column_name (str): The name of the column.

        Returns:
        The value at the specified row and column, or None if not found.
        """
        try:
            return df.get(column_name)[row]
            #return df.at[row_index, column_name]
        except KeyError:
            print(f"Column '{column_name}' not found.")
            return None
        except IndexError:
            print(f"Row index '{row_index}' is out of bounds.")
            return None
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
    def serialize_object(self, obj):
        """Recursively convert an object to a JSON-serializable dictionary."""
        if isinstance(obj, dict):
            return {k: self.serialize_object(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.serialize_object(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return self.serialize_object(vars(obj))  # Use vars() for better compatibility
        else:
            return obj  # Return the object as-is if it's already a serializable type

    def process_posts(self, posts):
        # Initialize posts_dicts
        posts_dicts = []

        # Check if posts is a list or a dict
        if isinstance(posts, dict):
            # If it's a dictionary, convert it to a list of its items
            posts_dicts = [self.serialize_object({k: v for k, v in posts.items()})]
        elif isinstance(posts, list):
            # If it's a list, iterate over the items
            for post in posts:
                posts_dicts.append(self.serialize_object(post))
        else:
            # Handle case where posts is a string or some other type
            posts_dicts.append(self.serialize_object(posts))

        return posts_dicts  # Return the processed posts
if __name__ == '__main__':
    arr = input('list (a_b) ')
    arr = list(arr.split('_'))
    util = Utilities()
    s = input('Search ')
    r = util.regex_search(arr, s)
    print(r)