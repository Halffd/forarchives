import asyncio
import aiohttp
from moesearch.parser import *
from moesearch.exceptions import ArchiveException

FOOLFUUKA_API_URL = "%s/_/api/chan"

async def fetch_json(session, url, params=None):
    async with session.get(url, params=params) as req:
        """if req.status < 300:
            try:
                print(f"Error fetching {url}: {req.status} {await req.text()}")
            except Exception as e:
                print(e + f"\nError fetching {url}: {req.status}")
            return None  # or raise an exception"""
        content_type = req.headers.get('Content-Type', '')
        try:
            if 'application/json' in content_type:
                res = await req.json()
                if ArchiveException.is_error(res):
                    # print(f'ArchiveException: {res}')
                    return None
                return res
            else:
                print(f"Unexpected content type: {content_type}")
                print(f"Response status: {req.status}")
                html_content = await req.text()  # Get the response text for debugging
                print(f"Response content: {html_content}")
                return None
        except Exception as e:
            print(f'Error in fetch: {e}')
            return e
async def index(archiver_url, board, page=1):
    async with aiohttp.ClientSession() as session:
        url = f"{FOOLFUUKA_API_URL % archiver_url}/index"
        params = {"board": str(board), "page": int(page)}
        res = await fetch_json(session, url, params)

        if res is None:
            return None
            
        for thread_num in res:
            res[thread_num] = IndexResult(res[thread_num])
        return res 

async def search(archiver_url, board, **kwargs):
    url = f"{FOOLFUUKA_API_URL % archiver_url}/search"
    try:
        kwargs["boards"] = board.lower()  # it's a string?
    except AttributeError:
        try:
            kwargs["boards"] = ".".join([str(b) for b in board])  # we got a list of boards!
        except TypeError:  # not iterable, try to convert
            kwargs["boards"] = str(board)

    async with aiohttp.ClientSession() as session:
        res = await fetch_json(session, url, params=kwargs)

        if res is None:
            return None
            
        res = res['0']
        return [Post(post_obj) for post_obj in res["posts"]]

async def thread(archiver_url, board, thread_num, latest_doc_id=-1, last_limit=-1):
    url = f"{FOOLFUUKA_API_URL % archiver_url}/thread"
    payload = {"board": str(board), "num": thread_num}
    if latest_doc_id != -1:
        payload["latest_doc_id"] = int(latest_doc_id)
    if last_limit != -1:
        payload["last_limit"] = int(last_limit)

    async with aiohttp.ClientSession() as session:
        res = await fetch_json(session, url, params=payload)

        if res is None:
            return None
            
        try:
            return Thread(res)
        e

async def post(archiver_url, board, post_num):
    async with aiohttp.ClientSession() as session:
        url = f"{FOOLFUUKA_API_URL % archiver_url}/post"
        params = {"board": str(board), "num": post_num}
        res = await fetch_json(session, url, params=params)

        if res is None:
            return None
            
        return Post(res)
# Example of how to run your async functions
async def main():
    archiver_url = "https://desuarchive.org"
    board = "/a/"
    results = await search(archiver_url, board, text='kson')
    print(results)

# To execute the async main function
if __name__ == "__main__":
   asyncio.run(main())