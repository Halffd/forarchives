# __init__.py

# Import the MoeSearcher class so it's accessible at the package level
from .moesearcher import MoeSearcher
from .async_api import search, thread, post
from .utilities import Utilities

__all__ = [
    'MoeSearcher',
    'search',
    'thread',
    'post',
    'Utilities'
]

# Optionally, you can include any package-level metadata here
__version__ = '1.0.0'
__author__ = 'Half'
__description__ = 'A package for searching and processing posts from various archives.'

# You can also initialize any required setup here if needed