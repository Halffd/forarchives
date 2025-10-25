"""
Exception classes for moesearch functionality
"""


class ArchiveException(Exception):
    @staticmethod
    def is_error(response):
        """
        Check if the response indicates an error.
        
        Args:
            response: The response from the archive API
            
        Returns:
            bool: True if response indicates an error, False otherwise
        """
        if isinstance(response, dict):
            # Check for common error indicators in the response
            if 'error' in response or response.get('status') == 'error':
                return True
            # Add other error checking logic as needed
        return False