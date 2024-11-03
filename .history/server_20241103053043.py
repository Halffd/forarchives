import tornado.ioloop
import tornado.web
import moesearch
import requests
from bs4 import BeautifulSoup
import search.moesearcher

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class SearchHandler(tornado.web.RequestHandler):
    def post(self):
        query = self.get_argument("query")
        board = self.get_argument("board", "a")  # Default to board 'a'
        
        
        # Define the URLs and their corresponding names
        archivers = {
            "desuarchive": "https://desuarchive.org",
            "4plebs": "https://archive.4plebs.org",
            "archived": "https://archived.moe",
            "palanq": "https://archive.palanq.win"
        }

        results = []

        # Loop through the archivers and collect results
        for name, url in archivers.items():
            search_results = moesearch.search(archiver_url=url, board=board, text=query)
            results.append({
                "source": name,
                "board": board,
                "results": search_results
            })
        
        # Optionally, scrape other archives
        other_results = self.scrape_other_archives(query)

        # Group results by source URL
        grouped_results = {}
        for result in results:
            source = result["source"]
            if source not in grouped_results:
                grouped_results[source] = {
                    "board": result["board"],
                    "results": result["results"]
                }
            else:
                grouped_results[source]["results"].extend(result["results"])

        # Combine the grouped results and other results
        final_results = {
            "grouped_results": grouped_results,
            "other_results": other_results
        }

        self.write(final_results)
        
    def scrape_other_archives(self, query):
        # Example scraping from other archives
        # This is a simple placeholder; you'll need to customize it to fit the specific archive structure
        scraped_results = []
        urls = [
            "https://warosu.org/jp/search/text/",
            "https://arch.b4k.co/_/search/text/"
        ]
        
        for url in urls:
            response = requests.get(url + query)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Parse the results based on the HTML structure of the page
                for post in soup.find_all("div", class_="post"):
                    title = post.find("h1", class_="post-title").text if post.find("h1", class_="post-title") else "No Title"
                    link = post.find("a", class_="post-link")["href"]
                    scraped_results.append({"title": title, "link": link})

        return scraped_results

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/search", SearchHandler),
    ], template_path="templates")

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()