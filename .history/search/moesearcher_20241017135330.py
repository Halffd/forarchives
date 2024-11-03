from async_api import *
from moesearch.parser import *
import requests
import asyncio
import aiohttp
from datetime import datetime
from utilities import Utilities
import pandas as pd

import pandas as pd
import json

class MoeSearcher:

    def __init__(self):
        global print
        self.archivers = {
            "desuarchive": "https://desuarchive.org",
            "palanq": "https://archive.palanq.win",
            "moe": "https://archived.moe",
            "4plebs": "https://archive.4plebs.org"
        }
        self.utilities = Utilities()
        print = self.utilities.printLog
    
    async def dumpster(self, posts):
        """Extract relevant data from posts and return as a DataFrame."""
        data = [
            {
                "timestamp": post.timestamp,
                "comment": post.comment,
                "country": post.poster_country_name,
                "thread_num": getattr(post, 'thread_num', None),
                "board": post.board.short_name if post.board else None
            }
            for post in posts
        ]
        
        # Create DataFrame from extracted data
        df = pd.DataFrame(data)
        return df

    async def search_and_dumpster(self, **kwargs):
        """Perform a search and process the results using the dumpster function."""
        posts = await self.search(**kwargs)
        df = await self.dumpster(posts)

        # Log the DataFrame as both text and JSON
        self.log_dataframe(df, query=kwargs.get('text', ''), folderName='dumpster')
        return df

    def log_dataframe(self, df, query='', folderName=''):
        """Log DataFrame contents to both JSON and plain text formats."""
        log_file = self.utilities.get_log_file('dumpster', '', query, folderName)
        obj = df.to_json(f"{log_file}.json", orient='records', lines=True, date_format='iso')
        # Save as plain text for readability
        self.utilities.log(df.to_string(), query=query,folderName=folderName)
        print(f"Data logged to {log_file}")
    def getArchive(self, archive=0):
        archiver_names = list(self.archivers.keys())
        if isinstance(archive, int):
            if 0 <= archive < len(archiver_names):
                return self.archivers[archiver_names[archive]]
            raise IndexError("Archive index out of range.")
        return archive

    def posts_to_dataframe(self, posts, folderName='dumpster', **kwargs):
        """Convert post data to a DataFrame."""
        if not posts:
            return pd.DataFrame()
        df = pd.DataFrame(self.utilities.process_posts(posts))
        queries = '-'.join(f"{key}-{value}" for key, value in kwargs.items())
        self.log_dataframe(df, query=queries, folderName=folderName)
        return df

    async def fetch_search_result(self, session, archive, board, page, **kwargs):
        return await search(archive, board=board, page=page, **kwargs)
    async def search(self, archive: int = 0, **kwargs) -> pd.DataFrame:
        """Perform search across a specific archive."""
        posts = []
        limit = kwargs.pop('limit', None)
        board = kwargs.pop('board', '_')
        delay = kwargs.pop('delay', 3.0)
        semaphore_limit = kwargs.pop('semaphore', 5)

        archive_url = self.getArchive(archive)
        semaphore = asyncio.Semaphore(semaphore_limit)

        async with aiohttp.ClientSession() as session:
            page = 1  # Start with page 1

            while True:
                # Create new tasks within each iteration to avoid reuse errors
                tasks = [
                    asyncio.create_task(
                        self.fetch_search_result(session, archive_url, board, page + i, **kwargs)
                    )
                    for i in range(semaphore_limit)
                ]

                # Gather the results from all tasks
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Collect only valid results
                valid_results = [res for res in results if isinstance(res, list) and res]

                if not valid_results:
                    break  # Exit if no more results

                posts.extend(valid_results)

                if limit and len(posts) >= limit:
                    return self.posts_to_dataframe(posts[:limit], 'search', board=board)

                page += semaphore_limit  # Increment the page number by semaphore limit

                # Introduce a non-blocking delay
                await asyncio.sleep(delay)

        return self.posts_to_dataframe(posts, 'search', board=board)

    async def multiArchiveSearch(self, archives=[0, 1, 2, 3], **query):
        tasks = [self.search(archive=idx, **query) for idx in archives]
        search_results = await asyncio.gather(*tasks)

        results = pd.concat(search_results, keys=[self.getArchiveName(i) for i in archives])
        self.utilities.log(results.to_string(), folderName='multi')
        self.log_dataframe(results, query=kwargs.get('text', ''), folderName='dumpster')

        return results

    async def calculate_statistics(self, results, text='', specific_board=None, specific_date=None):
        if results.empty:
            return 0, 0, 0.0, None

        # Convert date column to datetime
        results['date'] = pd.to_datetime(results['fourchan_date'], errors='coerce')
        valid_results = results.dropna(subset=['date'])

        if specific_board:
            valid_results = valid_results[valid_results['board'] == specific_board]

        if specific_date:
            date_filter = (
                valid_results['date'] < specific_date[1] if specific_date[0] == 'before' 
                else valid_results['date'] > specific_date[1]
            )
            valid_results = valid_results[date_filter]

        total_posts = len(valid_results)
        posts_with_text = valid_results['comment'].str.contains(text, na=False).sum()

        percentage = (posts_with_text / total_posts * 100) if total_posts > 0 else 0
        mean_date = valid_results['date'].mean()

        return total_posts, posts_with_text, percentage, mean_date

    async def fetch_thread(self, session, archive_url, board, thread_num, semaphore, delay, **kwargs):
        async with semaphore:
            await asyncio.sleep(delay)
            return await thread(archive_url, board=board, thread_num=thread_num, **kwargs)

    def getTextArray(self, posts_df):
        """Convert posts DataFrame to text format."""
        if posts_df.empty:
            return []

        return posts_df.apply(
            lambda row: f"{row['num']} {row['fourchan_date']} {row.get('title', '')}\n{row['comment']}", axis=1
        ).tolist()

    def formatText(self, df, delim='\n\n'):
        return delim.join(self.getTextArray(df))

    def qSearch(self, archive=0, **kwargs):
        """Run a quick search synchronously and return results as DataFrame."""
        return asyncio.run(self.search(archive, **kwargs))

    def req(self):
        """Synchronous search request with requests library."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
        }
        session = requests.Session()
        session.headers.update(headers)
        url = "https://archive.4plebs.org/_/api/chan/search"
        response = session.get(url, params={'text': 'x'})

        if response.status_code == 200:
            print(pd.DataFrame(response.json()).to_string())
        else:
            print(f"Error {response.status_code}: {response.text}")
    def getArchiveText(self, posts):
        try:
            result = []
            if isinstance(posts, Thread):
                i = [posts.op, *posts.posts]
                return self.getTextArray(i)
            elif not isinstance(posts, list):
                for k in posts:
                    i = posts[k].posts
                    if i:
                        if isinstance(i, list):
                            return self.getTextArray(i)
                        text = i.comment.replace('\n', '\n')
                        if text:
                            result.append(text)
            else:
                if len(posts) > 0:
                    if posts[0].thread_num:
                        result = [f'Thread: {posts[0].thread_num}']
                for i in posts:
                    text = ''
                    if i.title:
                        text += i.title + '\n'
                    if i.poster_country_name:
                        country = ' ' + i.poster_country_name
                    else:
                        country = ''
                    text += f'{i.num} {i.fourchan_date}{country}\n{i.comment}'
                    
                    if text:
                        result.append(text)
            return result
        except Exception as e:
            print(e)
            return None
    async def searchInSubject(self, archive=0, subject='', searchText='', **kwargs):
        archive_url = self.getArchive(archive)
        limit = kwargs.pop('limit', None)
        async with aiohttp.ClientSession() as session:
            tasks = []
            tasks.append(self.search(archive=archive_url, subject=subject, limit=limit, **kwargs))

            inBoth = kwargs.pop('inBoth', False)
            if inBoth:
                kwargs.pop('text')
                tasks.append(self.search(archive=archive_url, text=subject, type='op', limit=limit, **kwargs))

            results = await asyncio.gather(*tasks)

            # Process results
            if len(results) == 2:
                subjects, both_subjects = results
                subjects.extend(both_subjects)
            elif len(results) == 1:
                subjects = results[0]
                both_subjects = None
            else:
                subjects = []
                both_subjects = None

            board = kwargs.pop('board', '_')
            case = kwargs.pop('case', False)
            result = []
            searchesCount = 0
            thread_tasks = []
            semaphore_limit = kwargs.pop('semaphore', 5)  # Default semaphore limit if not provided
            delay = kwargs.pop('delay', 5.0)  # Default delay if not provided

            semaphore = asyncio.Semaphore(semaphore_limit)  # Limit concurrent tasks
            print(subjects.columns)
            print(subjects.head())

            si = -1
            for index in subjects.values:
                for ind
                si += 1
                threadN = index
                print(f'{si}/{len(subjects)}: {threadN}')
                if threadN is None:
                    continue
                board = self.utilities.df_get(subjects, index, 'board')
                if board is not None:
                    board = board.get('short_name') if isinstance(board, dict) else None
                if board is None:
                    board = '_'
                thread_tasks.append(asyncio.create_task(self.fetch_thread(session, archive_url, board, threadN, semaphore, delay, **kwargs)))

            threads = await asyncio.gather(*thread_tasks)
            if threads == []:
                return None
            print(threads.columns)
            print(threads.head())

            subjs = []
            for thr in threads:
                texts = self.formatText(thr)
                searched = self.utilities.regex_search(texts, searchText, case)
                subjs.append(texts)
                if searched:
                    searchedCount = len(searched)
                    searchesCount += searchedCount
                    found = [f'Thread: {threadN}, Count: {searchedCount}', *searched]
                    result.append(found)

            if result != []:
                result.insert(0, f'Total Count: {searchesCount} in {len(result)} threads')
            self.utilities.log(f"Search in subject '{subject}' returned {searchesCount} results.\n{self.formatText(result)}", 
                            site=self.getArchiveName(archive) + '_searches', board=board, query=searchText + '_' + subject, folderName='search-subjects')
            self.utilities.log(f"Search in subject '{subject}' returned {searchesCount} results.\n{self.formatText(subjs)}", 
                            site=self.getArchiveName(archive) + '_subjects', board=board, query=searchText + '_' + subject, folderName='subjects')
            return result

    async def fetch_thread(self, session, archive_url, board, thread_num, semaphore, delay, **kwargs):
        async with semaphore:
            # Introduce a delay before each request
            await asyncio.sleep(delay)
            thr =  await thread(archive_url, board=board, thread_num=thread_num, **kwargs)
            df = self.posts_to_dataframe(thr, 'thread', board=board)
            return df
    def getArchive(self, archive=0):
        if isinstance(archive, int):
            index = archive
            archiver_names = list(self.archivers.keys())
            
            if index < 0 or index >= len(archiver_names):
                raise IndexError("Index out of range.")
            
            archiver_name = archiver_names[index]
            return self.archivers[archiver_name]
        else:
            return archive

    def getArchiveName(self, archive):
        return list(self.archivers.keys())[archive] if isinstance(archive, int) else archive

    async def multiArchiveSearch(self, archives=[0, 1, 2, 3], **query):
        results = []
        tasks = []

        for index in archives:
            archive_url = self.getArchive(index)
            tasks.append(self.search(archive=archive_url, **query))

        # Gather all search results simultaneously
        search_results = await asyncio.gather(*tasks)

        for index, search_result in enumerate(search_results):
            if search_result:
                results.append({
                    "source": self.getArchiveName(index),
                    "board": query.get('board', '_'),
                    "results": search_result,
                    "text": self.formatText(search_result)
                })
        self.utilities.log(f'Searched {query}, {len(results)} found\n', board=query.get('board', ''), query=query.get('text', ''), folderName='search-multi')
        for i in results:
            posts = i['text']
            posts = '\n'.join(posts)
            self.utilities.log(f'/{i['board']}/\n{posts}', board=query.get('board', ''), query=query.get('text', ''), folderName='multi')
        grouped_results = self.groupArchives(results)
        self.utilities.json(grouped_results, 
                           site="multi", board=query.get('board', '_'),
                           query=query.get('subject', 'N/A'), folderName='multi')
        self.utilities.log(f"Multi-archive search returned results from {len(grouped_results)} archives.", 
                           site="multi", board=query.get('board', '_'),
                           query=query.get('subject', 'N/A'), folderName='multi')
        return grouped_results
    def groupArchives(self, results):
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
        return grouped_results
    def qSearch(self, archive=0, **kwargs):
        """Run a quick search synchronously and log the results."""
        search_results = asyncio.run(self.search(archive, **kwargs))
        
        return search_results
    def formatText(self, arr, delim = '\n\n', canPrint = False):
        text = ''
        for i, j in enumerate(arr):
            if canPrint:
                print(f'{i}: {j}{delim}')
            text += f'{j}{delim}'
        return text
    def toText(self, val, delim='\n\n', reverse=False, canPrint = False):
        arr = self.getTextArray(val)
        if reverse:
            arr.reverse()
        return self.formatText(arr, delim, canPrint)
# Example usage
if __name__ == '__main__':
    searcher = MoeSearcher()
    #p = asyncio.run(post(searcher.getArchive(0), 'a', 271697570))
    #df = searcher.posts_to_dataframe(p)
    results = searcher.qSearch(0, text='sylphy mushoku umaru')
    #results = searcher.qSearch(0, text='aparecida', limit=35)
    #print(results)
    #print(searcher.getText(results))
    
    results = asyncio.run(searcher.searchInSubject(0, subject='mushoku', searchText='"fitz"'))
    print(results)

    query = 'fortnite "hunger games" minecraft'
    grouped_results = asyncio.run(searcher.multiArchiveSearch([0, 1], text=query))
    
    total_posts, posts_with_text, percentage, mean_date = asyncio.run(searcher.calculate_statistics(grouped_results, '+'))
    print(f"Total posts: {total_posts}")
    print(f"Posts with text: {posts_with_text}")
    print(f"Percentage of posts with text: {percentage:.2f}%")
    print(f"Mean date of posts: {mean_date}")