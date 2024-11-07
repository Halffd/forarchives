import tornado.ioloop
import tornado.web
import asyncio
import pandas as pd
from bs4 import BeautifulSoup
import search.moesearcher as ms  # Ensure MoeSearcher is accessible via this path
import json
import requests

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        # Serve the main search page
        self.render("index.html")
class StaticFileHandler(tornado.web.StaticFileHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")

class SearchHandler(tornado.web.RequestHandler):
    async def post(self):
        # Get search query from form
        query = self.get_argument("query", "")
        archives = self.get_argument("archives", "[]")  # Expect a JSON array of archive IDs
        archives = json.loads(archives)

        moe_searcher = ms.MoeSearcher()
        try:
            # If multiple archives are selected, use multiArchiveSearch
            if len(archives) > 1:
                search_results = await moe_searcher.multiArchiveSearch(archives=archives, text=query)
            else:
                # Fetch results from the single selected archive
                search_results = await moe_searcher.search(archive=archives[0], text=query)

            results = []  # Initialize results list

            # Check if search_results is a DataFrame
            if isinstance(search_results, pd.DataFrame):
                results = search_results.to_dict(orient="records") if not search_results.empty else []
            elif isinstance(search_results, dict):
                # If it's a dictionary, loop through each archive's results
                for archive_name, archive_data in search_results.items():
                    board = archive_data.get('board', '_')
                    for result in archive_data.get('results', []):
                        results.append({
                            "source": archive_name,
                            "board": board,
                            **result  # Assuming result is already a dict containing the post info
                        })

            self.write({"results": results})
        except Exception as e:
            self.write({"error": str(e)})

    def scrape_other_archives(self, query):
        # Example of a simple synchronous scraping method for other archives
        scraped_results = []
        urls = [
            "https://warosu.org/jp/search/text/",
            "https://arch.b4k.co/_/search/text/"
        ]
        
        for url in urls:
            response = requests.get(url + query)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                for post in soup.find_all("div", class_="post"):
                    title = post.find("h1", class_="post-title").text if post.find("h1", class_="post-title") else "No Title"
                    link = post.find("a", class_="post-link")["href"]
                    scraped_results.append({"title": title, "link": link})

        return scraped_results

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/search", SearchHandler),
        (r"/static/(.*)", StaticFileHandler, {"path": "static"}),
    ], template_path="templates", debug=True)

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("Server running on http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()
