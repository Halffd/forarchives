from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import json
import redis
import hashlib
import time
import os
from pathlib import Path
from search.moesearcher import MoeSearcher


class RedisCacheManager:
    def __init__(self, host='localhost', port=6379, db=0, password=None, default_ttl=3600):
        self.redis_client = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True)
        self.default_ttl = default_ttl  # Default TTL in seconds (1 hour)

    def generate_cache_key(self, params):
        """Generate a cache key based on search parameters"""
        # Create a string representation of the parameters
        param_str = f"{params.get('query', '')}_{params.get('archives', [])}_{params.get('board', '_')}_{params.get('useRegex', False)}_{params.get('limit', 50)}_{params.get('subjectOnly', False)}"
        # Create a hash of the parameters to ensure consistent key format
        return hashlib.md5(param_str.encode()).hexdigest()

    def get_cached_result(self, cache_key):
        """Get cached result by key"""
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            print(f"Error getting cached result: {e}")
            return None

    def set_cached_result(self, cache_key, result, ttl=None):
        """Set cached result with TTL"""
        try:
            ttl = ttl or self.default_ttl
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result, default=str)  # Use default=str to handle datetime objects
            )
        except Exception as e:
            print(f"Error setting cached result: {e}")

    def is_cache_warm(self):
        """Check if Redis is available"""
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False


# Initialize the cache manager
cache_manager = RedisCacheManager()


@api_view(['POST'])
@permission_classes([AllowAny])
def search_view(request):
    try:
        data = request.data
        query = data.get("query", "")
        archives = data.get("archives", [])
        board = data.get("board", "_")  # Default to all boards
        use_regex = data.get("useRegex", False)
        limit = data.get("limit", 50)
        subject_only = data.get("subjectOnly", False)

        # Generate cache key based on search parameters
        cache_key = cache_manager.generate_cache_key({
            "query": query,
            "archives": archives,
            "board": board,
            "useRegex": use_regex,
            "limit": limit,
            "subjectOnly": subject_only
        })

        # Try to get cached result first
        cached_result = cache_manager.get_cached_result(cache_key)
        if cached_result:
            print(f"Cache hit for query: {query}")
            return Response({"results": cached_result, "cached": True})

        # If not in cache, perform the search
        moe_searcher = MoeSearcher()
        
        # Prepare search parameters
        search_kwargs = {
            "text": query,
            "board": board,
            "limit": limit
        }
        
        # Add regex parameter if supported by the search method
        if use_regex:
            search_kwargs["regex"] = query  # This would need to be handled by the backend
        
        # Add subject only parameter if needed
        if subject_only:
            search_kwargs["subject"] = query  # Search in subject field

        if len(archives) > 1:
            search_results = moe_searcher.multiArchiveSearch(archives=archives, **search_kwargs)
        else:
            search_results = moe_searcher.search(archive=archives[0], **search_kwargs)

        # Process the results (this function should be adapted from the original server)
        processed_results = process_results(search_results)
        
        # Cache the results (only if caching is available)
        if cache_manager.is_cache_warm():
            cache_manager.set_cached_result(cache_key, processed_results)
            print(f"Result cached for query: {query}")
        else:
            print("Redis not available, skipping cache")

        return Response({"results": processed_results, "cached": False})
    except Exception as e:
        return Response({"error": str(e)}, status=500)


def process_results(search_results):
    """Process search results into the format expected by the frontend"""
    results = []
    
    # Handle different result formats
    if hasattr(search_results, 'to_dict') and callable(getattr(search_results, 'to_dict')):
        # If it's a pandas DataFrame
        results = search_results.to_dict(orient="records")
    elif isinstance(search_results, dict):
        # If it's a dictionary with archive keys
        for archive_name, archive_data in search_results.items():
            board = archive_data.get('board', '_')
            for result in archive_data.get('results', []):
                results.append({
                    "source": archive_name,
                    "board": board,
                    **result
                })
    elif isinstance(search_results, list):
        # If it's already a list of results
        results = search_results
    else:
        # Default case
        results = []

    return results


def serve_frontend(request, *args, **kwargs):
    """
    Serve the Angular frontend for all non-API routes.
    This catches all routes that aren't API endpoints and serves the Angular app.
    """
    # Path to the built Angular app - use absolute path from project root
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    frontend_dir = os.path.join(base_dir, 'dist', 'forarchives', 'browser')
    
    # Default file to serve
    file_path = os.path.join(frontend_dir, 'index.html')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("Frontend not found. Please build the Angular application.", status=404)
