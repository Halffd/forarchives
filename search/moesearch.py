"""
Data classes for moesearch functionality
"""


class Post:
    def __init__(self, data):
        # Initialize with data dictionary
        for key, value in data.items():
            setattr(self, key, value)
    
    def __repr__(self):
        return f"Post({self.__dict__})"


class Thread:
    def __init__(self, data):
        # Initialize with data dictionary
        for key, value in data.items():
            setattr(self, key, value)
    
    def __repr__(self):
        return f"Thread({self.__dict__})"