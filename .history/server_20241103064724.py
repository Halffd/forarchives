import tornado.ioloop
import tornado.web
import asyncio
import pandas as pd
from bs4 import BeautifulSoup
import search.moesearcher as ms  # Ensure MoeSearcher is accessible via this path
import json
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        # Serve the main search page
        self.render("index.html")

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

            # Convert DataFrame to a dictionary for easy JSON rendering
            results = search_results.to_dict(orient="records") if not search_results.empty else []
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
    ], template_path="templates", debug=True)

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("Server running on http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()
