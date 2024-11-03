# __init__.py

# Import the MoeSearcher class so it's accessible at the package level
from .moesearcher import MoeSearcher

__all__ = ['MoeSearcher']  # This defines what will be imported if someone does 'from your_package import *'

# Optionally, you can include any package-level metadata here
__version__ = '1.0.0'
__author__ = 'Your Name'
__description__ = 'A package for searching and processing posts from various archives.'

# You can also initialize any required setup here if needed