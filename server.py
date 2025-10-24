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

class AngularHandler(tornado.web.StaticFileHandler):
    def parse_url_path(self, url_path):
        """Serve index.html for all Angular routes"""
        if not url_path or not os.path.exists(os.path.join(self.root, url_path)):
            return 'index.html'
        return url_path

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

            moe_searcher = MoeSearcher()
            
            if len(archives) > 1:
                search_results = await moe_searcher.multiArchiveSearch(archives=archives, text=query)
            else:
                search_results = await moe_searcher.search(archive=archives[0], text=query)

            self.write({"results": self.process_results(search_results)})
        except Exception as e:
            self.write({"error": str(e)})

    def process_results(self, search_results):
        results = []
        if isinstance(search_results, pd.DataFrame):
            results = search_results.to_dict(orient="records")
        elif isinstance(search_results, dict):
            for archive_name, archive_data in search_results.items():
                board = archive_data.get('board', '_')
                for result in archive_data.get('results', []):
                    results.append({
                        "source": archive_name,
                        "board": board,
                        **result
                    })
        return results

def make_app(is_desktop=False):
    settings = {
        "debug": True,
        "static_path": STATIC_PATH,
        "template_path": TEMPLATE_PATH
    }

    if is_desktop:
        settings["static_path"] = ANGULAR_DIST

    handlers = [
        (r"/api/search", SearchHandler),
        (r"/manifest\.webmanifest", tornado.web.StaticFileHandler, {"path": ANGULAR_DIST}),
        (r"/ngsw\.json", tornado.web.StaticFileHandler, {"path": ANGULAR_DIST}),
        (r"/ngsw-worker\.js", tornado.web.StaticFileHandler, {"path": ANGULAR_DIST}),
        (r"/safety-worker\.js", tornado.web.StaticFileHandler, {"path": ANGULAR_DIST}),
        (r"/worker-basic\.min\.js", tornado.web.StaticFileHandler, {"path": ANGULAR_DIST}),
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
