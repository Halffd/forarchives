import tornado.ioloop
import tornado.web
import requests
from bs4 import BeautifulSoup
import search.moesearcher as ms                                                                                 

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class SearchHandler(tornado.web.RequestHandler):
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