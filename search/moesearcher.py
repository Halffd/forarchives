from async_api import *
from moesearch.parser import *
import requests
import asyncio
import aiohttp
from datetime import datetime
from utilities import Utilities

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
    def getText(self, posts):
        try:
            result = []
            if isinstance(posts, Thread):
                i = [posts.op, *posts.posts]
                return self.getText(i)
            elif not isinstance(posts, list):
                for k in posts:
                    i = posts[k].posts
                    if i:
                        if isinstance(i, list):
                            return self.getText(i)
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
    async def fetch_search_result(self, session, archive, board, page, **kwargs):
        return await search(archive, board=board, page=page, **kwargs)
    async def search(self, archive=0, **kwargs):
        posts = []
        limit = kwargs.pop('limit', None)
        board = kwargs.pop('board', '_')
        delay = kwargs.pop('delay', 3.0)  # Default delay if not provided
        semaphore_limit = kwargs.pop('semaphore', 5)  # Default semaphore limit if not provided
        archive_url = self.getArchive(archive)

        semaphore = asyncio.Semaphore(semaphore_limit)  # Limit concurrent tasks
        i = 1
        last_results = None
        
        async with aiohttp.ClientSession() as session:
            while True:
                tasks = []  # Create a new list for tasks each iteration
                
                for _ in range(semaphore_limit):
                    async with semaphore:
                        task = self.fetch_search_result(session, archive_url, board, i, **kwargs)
                        tasks.append(task)
                        i += 1
                    
                    # Introduce a delay between requests
                    await asyncio.sleep(delay)

                    if limit and len(tasks) >= limit:
                        break

                if not tasks:  # No more tasks to process
                    break
                print(f'{i}: {len(tasks)} {limit}')
                # Gather results for the current batch
                results = await asyncio.gather(*tasks)

                if last_results is not None and not any(results):
                    # If the last batch had no results, stop further requests
                    break

                last_results = results
                for result in results:
                    if result:
                        posts.extend(result)
                        if limit and len(posts) >= limit:
                            return posts[:limit]
                    else:
                        break  # If no result, stop further requests
        # Prepare log message and log the results
        text = 'search'
        text += kwargs.pop('-text', '')
        text += kwargs.pop('-subject', '')
        site = self.utilities.key_by_value(self.archivers, archive_url)
        posts_dicts = self.utilities.process_posts(posts)
        # Log the search results
        self.utilities.json(
            posts_dicts,
            site=site,
            board=board,
            query=text,
            folderName='search'
        )
        self.utilities.log(
            message=self.toText(posts),
            site=site,
            board=board,
            query=text,
            folderName='search'
        )
        
        return posts
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
            delay = kwargs.pop('delay', 3.0)  # Default delay if not provided

            semaphore = asyncio.Semaphore(semaphore_limit)  # Limit concurrent tasks
            si = -1
            for sub in subjects:
                si += 1
                threadN = sub.thread_num
                print(f'{si}/{len(subjects)}: {threadN}')
                if sub.board:
                    board = sub.board.short_name

                thread_tasks.append(asyncio.create_task(self.fetch_thread(session, archive_url, board, threadN, semaphore, delay, **kwargs)))

            threads = await asyncio.gather(*thread_tasks)
            subjs = []
            for thr in threads:
                texts = self.getText(thr)
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
            self.utilities.json(subjs, 
                            site=self.getArchiveName(archive) + '_searches', board=board, query=searchText + '_' + subject, folderName='search-subjects')
            self.utilities.json(result, 
                            site=self.getArchiveName(archive) + '_subjects', board=board, query=searchText + '_' + subject, folderName='subjects')
            return result

    async def fetch_thread(self, session, archive_url, board, thread_num, semaphore, delay, **kwargs):
        async with semaphore:
            # Introduce a delay before each request
            await asyncio.sleep(delay)
            return await thread(archive_url, board=board, thread_num=thread_num, **kwargs)
    async def searchFast(self, archive=0, **kwargs):
        posts = []
        limit = kwargs.pop('limit', None)
        board = kwargs.pop('board', '_')
        archive_url = self.getArchive(archive)

        async with aiohttp.ClientSession() as session:
            tasks = []
            i = 1
            
            while True:
                tasks.append(self.fetch_search_result(session, archive_url, board, i, **kwargs))
                i += 1
                
                if limit and len(tasks) >= limit:
                    break

            results = await asyncio.gather(*tasks)
            
            for result in results:
                if result:
                    posts.extend(result)
                    if limit and len(posts) >= limit:
                        return posts[:limit]
                else:
                    break

        return posts

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
                    "text": self.getText(search_result)
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

    async def calculate_statistics(self, grouped_results, text='', subject=None, specific_board=None, specific_date=['before', None]):
        total_posts = 0
        posts_with_text = 0
        post_dates = []

        for source, data in grouped_results.items():
            for post in data["results"]:
                # Check if the post date is valid and meets criteria
                try:
                    post_date = datetime.strptime(post.fourchan_date, '%m/%d/%y(%a)%H:%M')
                except ValueError as e:
                    print(f"Date parsing error for post: {post.fourchan_date} - {e}")
                    continue  # Skip this post if the date is invalid

                if (specific_board is None or post.board.name == specific_board) and \
                (specific_date is None or self.check_date(post_date, specific_date)):
                    total_posts += 1
                    post_dates.append(post_date)
                    if text in post.comment:
                        posts_with_text += 1
        
        # Calculate percentage
        percentage = (posts_with_text / total_posts * 100) if total_posts > 0 else 0
        
        # Calculate mean date
        mean_date = self.calculate_mean_date(post_dates) if post_dates else None
        if post_dates:
            # Create a graph
            self.utilities.plot_statistics(post_dates)

        return total_posts, posts_with_text, percentage, mean_date
    def check_date(self, post_date, specific_date):
        if specific_date == None:
            return 0
        if specific_date[0] == 'before':
            return post_date < specific_date[1]
        elif specific_date[0] == 'after':
            return post_date > specific_date[1]
        return True

    def calculate_mean_date(self, dates):
        if not dates:
            return None
        mean_timestamp = sum(date.timestamp() for date in dates) / len(dates)
        return datetime.fromtimestamp(mean_timestamp)

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

    def req(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
        }
        session = requests.Session()
        session.headers.update(headers)
        url = "https://archive.4plebs.org/_/api/chan/search"
        response = session.get(url, params={'text': 'x'})

        if response.status_code == 200:
            print(response.json())  # Assuming the response is JSON
        else:
            print(f"Error {response.status_code}: {response.text}")

    async def trysearch(self):
        try:
            search_results = await search("https://archive.4plebs.org", board="pol", text="brazil")
            if search_results:
                print(search_results[0].comment)
        except Exception as e:
            print(f"An error occurred: {e}")
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
        arr = self.getText(val)
        if reverse:
            arr.reverse()
        return self.formatText(arr, delim, canPrint)
# Example usage
if __name__ == '__main__':
    searcher = MoeSearcher()

    results = searcher.qSearch(0, text='trocr')
    #results = searcher.qSearch(0, text='aparecida', limit=35)
    #print(results)
    #print(searcher.getText(results))
    
    results = asyncio.run(searcher.searchInSubject(0, subject='', searchText='"film theory', board='a'))
    print(results)

    query = 'binomial|pull|gacha|lootbox|game'
    grouped_results = asyncio.run(searcher.multiArchiveSearch([0, 1], text=query))
    
    total_posts, posts_with_text, percentage, mean_date = asyncio.run(searcher.calculate_statistics(grouped_results, '+'))
    print(f"Total posts: {total_posts}")
    print(f"Posts with text: {posts_with_text}")
    print(f"Percentage of posts with text: {percentage:.2f}%")
    print(f"Mean date of posts: {mean_date}")