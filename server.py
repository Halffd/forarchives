import tornado.ioloop
import tornado.web
import asyncio
import pandas as pd
from bs4 import BeautifulSoup
from search.moesearcher import MoeSearcher
import json
import requests
from config import ANGULAR_DIST, STATIC_PATH, TEMPLATE_PATH
import os
import sys
import redis
import hashlib
import time


class AngularHandler(tornado.web.StaticFileHandler):
    def parse_url_path(self, url_path):
        """Serve index.html for all Angular routes"""
        if not url_path or not os.path.exists(os.path.join(self.root, url_path)):
            return "index.html"
        return url_path


class RedisCacheManager:
    def __init__(
        self, host="localhost", port=6379, db=0, password=None, default_ttl=3600
    ):
        self.redis_client = redis.Redis(
            host=host, port=port, db=db, password=password, decode_responses=True
        )
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
                json.dumps(
                    result, default=str
                ),  # Use default=str to handle datetime objects
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


class SearchHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def options(self):
        self.set_status(204)
        self.finish()

    async def post(self):
        try:
            data = json.loads(self.request.body)
            query = data.get("query", "")
            archives = data.get("archives", [])
            board = data.get("board", "_")  # Default to all boards
            use_regex = data.get("useRegex", False)
            limit = data.get("limit", 50)
            subject_only = data.get("subjectOnly", False)

            # Generate cache key based on search parameters
            cache_key = cache_manager.generate_cache_key(
                {
                    "query": query,
                    "archives": archives,
                    "board": board,
                    "useRegex": use_regex,
                    "limit": limit,
                    "subjectOnly": subject_only,
                }
            )

            # Try to get cached result first
            cached_result = cache_manager.get_cached_result(cache_key)
            if cached_result:
                print(f"Cache hit for query: {query}")
                self.write({"results": cached_result, "cached": True})
                return

            # If not in cache, perform the search
            moe_searcher = MoeSearcher()

            # Prepare search parameters
            search_kwargs = {"text": query, "board": board, "limit": limit}

            # Add regex parameter if supported by the search method
            if use_regex:
                search_kwargs["regex"] = (
                    query  # This would need to be handled by the backend
                )

            # Add subject only parameter if needed
            if subject_only:
                search_kwargs["subject"] = query  # Search in subject field

            if len(archives) > 1:
                search_results = await moe_searcher.multiArchiveSearch(
                    archives=archives, **search_kwargs
                )
            else:
                search_results = await moe_searcher.search(
                    archive=archives[0], **search_kwargs
                )

            # Process the results
            processed_results = self.process_results(search_results)

            # Cache the results (only if caching is available)
            if cache_manager.is_cache_warm():
                cache_manager.set_cached_result(cache_key, processed_results)
                print(f"Result cached for query: {query}")
            else:
                print("Redis not available, skipping cache")

            self.write({"results": processed_results, "cached": False})
        except Exception as e:
            self.write({"error": str(e)})

    def process_results(self, search_results):
        results = []
        if isinstance(search_results, pd.DataFrame):
            results = search_results.to_dict(orient="records")
        elif isinstance(search_results, dict):
            for archive_name, archive_data in search_results.items():
                board = archive_data.get("board", "_")
                for result in archive_data.get("results", []):
                    results.append({"source": archive_name, "board": board, **result})
        return results


def make_app(is_desktop=False):
    settings = {
        "debug": True,
        "static_path": STATIC_PATH,
        "template_path": TEMPLATE_PATH,
    }

    if is_desktop:
        settings["static_path"] = ANGULAR_DIST

    handlers = [
        (r"/api/search", SearchHandler),
        (
            r"/manifest\.webmanifest",
            tornado.web.StaticFileHandler,
            {"path": ANGULAR_DIST},
        ),
        (r"/ngsw\.json", tornado.web.StaticFileHandler, {"path": ANGULAR_DIST}),
        (r"/ngsw-worker\.js", tornado.web.StaticFileHandler, {"path": ANGULAR_DIST}),
        (r"/safety-worker\.js", tornado.web.StaticFileHandler, {"path": ANGULAR_DIST}),
        (
            r"/worker-basic\.min\.js",
            tornado.web.StaticFileHandler,
            {"path": ANGULAR_DIST},
        ),
        (r"/(.*)", AngularHandler, {"path": ANGULAR_DIST}),
    ]

    return tornado.web.Application(handlers, **settings)


if __name__ == "__main__":
    is_desktop = "--desktop" in sys.argv
    app = make_app(is_desktop)
    port = 8888
    app.listen(port)
    print(f"Server running on http://localhost:{port}")
    tornado.ioloop.IOLoop.current().start()
