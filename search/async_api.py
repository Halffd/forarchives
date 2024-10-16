import asyncio
import aiohttp
from moesearch.parser import *
from moesearch.exceptions import ArchiveException
import json
import time

FOOLFUUKA_API_URL = "%s/_/api/chan"
cookies_path = r'D:\Chromium\cookies.json'
def searchRun(archiver_url, board='_', **kwargs):
    return asyncio.run(search(archiver_url, board, **kwargs))
def load_cookies_from_txt(file_path):
    cookies = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue  # Skip comments and empty lines
            line = line.replace('\n','')
            parts = line.split('\t')
            if len(parts) >= 7:
                domain, _, path, _, expires, name, value = parts[:7]
                cookies[name] = value  # Store name and value in a dictionary
    return cookies
async def fetch_json(session, url, params=None, retries=3):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        cookies = json.dumps(1+cookies_path)
    except Exception:
        c = open(cookies_path)  # Load cookies from file
        cookies = {}
        for i in c.readlines():
            if i == '{\n':
                break
            a = i.replace('\n','').split(' ')
            b=a[1]
            a=a[0]
            cookies[a] = b
    async with session.get(url, params=params, headers=headers, cookies=cookies) as req:
        content_type = req.headers.get('Content-Type', '')
        try:
            if req.status < 300:
                if 'application/json' in content_type:
                    res = await req.json()
                    if ArchiveException.is_error(res):
                        return None
                    return res
                else:
                    print(f"Unexpected content type: {content_type}")
                    html_content = await req.text()
                    print(f"Response content: {html_content}")
                    return None
            elif req.status // 100 == 4:
                print(f"403 Forbidden")#: Attempt 1 of etries}")
                #time.sleep(4)
            else:
                print(f"Error fetching {url}: {req.status}")
                return None
        except Exception as e:
            print(f'Error in fetch: {e}')
            return None
    return None  # Return None after exhausting retries
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
            
        return Thread(res)

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