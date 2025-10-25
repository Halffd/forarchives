import asyncio
import aiohttp
from .moesearch import *
from .exceptions import ArchiveException
import time
import os
import json
import logging
from pathlib import Path
from bs4 import BeautifulSoup

# Optional imports that may not be available
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import browser_cookie3
    CHROMEDRIVER_AVAILABLE = True
except ImportError:
    CHROMEDRIVER_AVAILABLE = False
    print("Warning: undetected_chromedriver, selenium, or browser_cookie3 not available. Some functionality may be limited.")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # Changed from '4plebs_selenium' to module name

FOOLFUUKA_API_URL = "%s/_/api/chan"
SHOW_WINDOW = True

class PlebsSession:
    _instance = None
    _driver = None
    _cookies = None
    _last_init = 0
    _session = None
    INIT_COOLDOWN = 300  # 5 minutes
    
    @classmethod
    async def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
    
    def _setup_chrome_options(self):
        """Configure Chrome options for stealth operation"""
        if not CHROMEDRIVER_AVAILABLE:
            raise ImportError("undetected_chromedriver is not available. Please install it to use this functionality.")
        
        options = uc.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        # Set user agent explicitly
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        return options
    
    def _get_chrome_cookies(self):
        if not CHROMEDRIVER_AVAILABLE:
            logger.warning("browser_cookie3 not available, cannot get Chrome cookies")
            return []
        
        try:
            chrome_cookies = browser_cookie3.chrome(domain_name='4plebs.org')
            return [{'name': c.name, 'value': c.value, 'domain': c.domain} for c in chrome_cookies]
        except Exception as e:
            logger.warning(f"Could not get Chrome cookies: {e}")
            return []
    
    async def get_session(self):
        """Get or create aiohttp session with current cookies"""
        if not self._session:
            timeout = aiohttp.ClientTimeout(total=60)
            self._session = aiohttp.ClientSession(timeout=timeout)
            if self._cookies:
                self._session.cookie_jar.update_cookies(self.get_cookies_dict())
        return self._session
    
    async def wait_for_cloudflare(self, driver):
        """Wait for Cloudflare challenge to be solved"""
        if not CHROMEDRIVER_AVAILABLE:
            logger.error("Selenium not available, cannot wait for Cloudflare")
            return False
            
        logger.info("Waiting for Cloudflare challenge...")
        try:
            # Wait for the main content to be visible (after Cloudflare)
            WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.ID, "main"))
            )
            logger.info("Cloudflare challenge completed")
            return True
        except Exception as e:
            logger.error(f"Cloudflare wait failed: {e}")
            return False
    
    async def init_session(self, force=False):
        if not CHROMEDRIVER_AVAILABLE:
            logger.warning("Chrome driver not available, cannot initialize 4plebs session")
            return False
        
        current_time = time.time()
        if not force and self._last_init and (current_time - self._last_init) < self.INIT_COOLDOWN:
            if self._cookies:
                logger.info("Using existing session")
                return True
        
        if self._driver:
            logger.info("Browser already open, waiting for user interaction...")
            return True
            
        logger.info("Initializing 4plebs session with undetected-chromedriver...")
        
        try:
            def setup_driver():
                options = self._setup_chrome_options()
                driver = uc.Chrome(
                    options=options,
                    headless=False,  # Force showing window
                    use_subprocess=True
                )
                return driver
            
            self._driver = await asyncio.get_event_loop().run_in_executor(None, setup_driver)
            
            def load_page(driver):
                driver.get('https://archive.4plebs.org/')
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                return driver
            
            await asyncio.get_event_loop().run_in_executor(None, load_page, self._driver)
            
            print("\nBrowser window should be visible.")
            print("Please solve any Cloudflare challenges if they appear.")
            print("Press Enter once you've solved the challenge.\n")
            
            # Wait for user input
            await asyncio.get_event_loop().run_in_executor(None, input)
            
            # Get cookies after user interaction
            self._cookies = self._driver.get_cookies()
            self._last_init = time.time()
            
            if self._cookies:
                await self.close_driver()
                logger.info("Session initialized successfully")
                return True
            
            logger.warning("No cookies obtained, keeping browser open")
            return False
            
        except Exception as e:
            logger.error(f"Failed to initialize 4plebs session: {e}")
            await self.close()
            return False
    
    def get_cookies_dict(self):
        if not self._cookies:
            return {}
        return {cookie['name']: cookie['value'] for cookie in self._cookies}
    
    async def close_driver(self):
        """Close only the Selenium driver"""
        if self._driver:
            try:
                await asyncio.get_event_loop().run_in_executor(None, self._driver.quit)
            except Exception as e:
                logger.error(f"Error closing driver: {e}")
            finally:
                self._driver = None
    
    async def close(self):
        """Close both driver and session"""
        await self.close_driver()
        if self._session:
            try:
                await self._session.close()
            except Exception as e:
                logger.error(f"Error closing session: {e}")
            finally:
                self._session = None
        self._cookies = None

async def fetch_json(url, params=None, retries=2):
    """Fetch JSON with special handling for 4plebs"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    # Only use PlebsSession for 4plebs
    if '4plebs' in url:
        plebs_session = await PlebsSession.get_instance()
        session = await plebs_session.get_session()
    else:
        # Use regular session for other archives
        timeout = aiohttp.ClientTimeout(total=30)
        session = aiohttp.ClientSession(timeout=timeout)
    
    try:
        for attempt in range(retries + 1):
            try:
                async with session.get(url, params=params, headers=headers) as req:
                    text = await req.text()
                    
                    try:
                        res = json.loads(text)
                        if ArchiveException.is_error(res):
                            logger.warning(f'ArchiveException: {res}')
                            return None
                        return res
                    except json.JSONDecodeError:
                        if '4plebs' in url and any(x in text.lower() for x in ['captcha', 'javascript', 'cloudflare']):
                            if attempt < retries:
                                logger.info("4plebs protection detected - reinitializing session...")
                                await plebs_session.init_session(force=True)
                                continue
                        logger.error("Invalid JSON response")
                        return None
                        
            except Exception as e:
                logger.error(f'Error in fetch (attempt {attempt + 1}/{retries + 1}): {e}')
                if attempt < retries:
                    await asyncio.sleep(2)
                    continue
                return None
    finally:
        # Only close non-4plebs sessions
        if not '4plebs' in url and session:
            await session.close()
    
    return None

async def warosu_search(board, **kwargs):
    """Search Warosu archive"""
    # Clean up board name
    board = str(board).strip().lower().replace('/', '')
    
    # Construct URL with proper board and search parameters
    url = f"https://warosu.org/{board}"
    
    params = {
        "task": "search",
        "ghost": "false",
        "search_text": kwargs.get('text', '')  # Get text from kwargs
    }
    
    logger.info(f"Constructing Warosu search: {url} with params {params}")
    
    # Add optional search parameters
    if kwargs.get('subject'):
        params['search_subject'] = kwargs['subject']
    if kwargs.get('username'): 
        params['search_username'] = kwargs['username']
    if kwargs.get('filename'):
        params['search_filename'] = kwargs['filename']
    if kwargs.get('datefrom'):
        params['search_datefrom'] = kwargs['datefrom'] 
    if kwargs.get('dateto'):
        params['search_dateto'] = kwargs['dateto']
    if kwargs.get('limit'):
        params['limit'] = kwargs['limit']

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                logger.info(f"Warosu response status: {response.status}")
                if response.status != 200:
                    logger.error(f"Warosu returned status {response.status}")
                    return []
                
                html = await response.text()
                if not html:
                    logger.error("Empty response from Warosu")
                    return []
                    
                logger.info("Parsing Warosu HTML response")
                soup = BeautifulSoup(html, 'html.parser')
                
                posts = []
                # Look for posts in both replies and OPs
                for post_div in soup.select('.reply, .post-wrapper'):
                    try:
                        # Extract post number
                        post_link = post_div.select_one('a.js')
                        if not post_link:
                            continue
                        post_num = post_link.text.replace('No.', '')
                        
                        # Extract comment
                        comment_elem = post_div.select_one('blockquote')
                        comment = comment_elem.get_text(strip=True) if comment_elem else ''
                        
                        # Get timestamp 
                        time_elem = post_div.select_one('.posttime')
                        timestamp = int(time_elem['title']) if time_elem and 'title' in time_elem.attrs else 0
                        
                        # Get image if present
                        media = None
                        img_elem = post_div.select_one('.thumb')
                        if img_elem and img_elem.parent.name == 'a':
                            media = {
                                'media_link': img_elem.parent['href'],
                                'media_orig': img_elem['src'],
                                'media_filename': img_elem.get('alt', ''),
                                'media_w': None,
                                'media_h': None,
                                'media_size': None,
                                'media_hash': None,
                                'media_status': 'normal'
                            }
                        
                        # Create post data dictionary in FoolFuuka format
                        post_data = {
                            'num': post_num,
                            'timestamp': str(timestamp),
                            'comment': comment,
                            'media': media,
                            'board': {
                                'name': board,
                                'shortname': board  # Changed from short_name to shortname
                            },
                            'thread_num': post_num,  # For OPs this is the same as post_num
                            'poster_country': '',
                            'poster_country_name': '',
                            'poster_hash': '',
                            'name': 'Anonymous',
                            'title': '',
                            'trip': '',
                            'subnum': '0',
                            'op': 0,
                            'email': '',
                            'sticky': 0,
                            'locked': 0,
                            'deleted': 0
                        }
                        
                        posts.append(Post(post_data))
                        
                        # Respect limit if specified
                        if kwargs.get('limit') and len(posts) >= int(kwargs['limit']):
                            break
                            
                    except Exception as e:
                        logger.error(f"Error parsing Warosu post: {e}")
                        continue
                
                logger.info(f"Found {len(posts)} posts on Warosu")
                return posts
                
    except Exception as e:
        logger.error(f"Error searching Warosu: {e}")
        return []

async def search(archiver_url, board, **kwargs):
    """Search archives with special handling for different sites"""
    logger.info(f"Searching archive: {archiver_url} {board} {kwargs.get('text')}")
    
    # Convert archiver_url to string and normalize it
    archiver_url = str(archiver_url).lower().strip()
    
    # Handle Warosu searches
    if 'warosu' in archiver_url:
        logger.info(f"Starting Warosu search for board /{board}/ with text: {kwargs.get('text')}")
        try:
            # Don't extract text parameter separately since it's already in kwargs
            results = await warosu_search(board, **kwargs)
            logger.info(f"Warosu search completed with {len(results) if results else 0} results")
            return results
        except Exception as e:
            logger.error(f"Error in Warosu search: {e}")
            return []

    # Handle FoolFuuka archives
    try:
        url = f"{FOOLFUUKA_API_URL % archiver_url}/search"
        try:
            kwargs["boards"] = board.lower()
        except AttributeError:
            try:
                kwargs["boards"] = ".".join([str(b) for b in board])
            except TypeError:
                kwargs["boards"] = str(board)

        res = await fetch_json(url, params=kwargs)
        if res is None:
            return None
            
        res = res['0']
        return [Post(post_obj) for post_obj in res["posts"]]
    except Exception as e:
        logger.error(f"Error in FoolFuuka search: {e}")
        return None

async def thread(archiver_url, board, thread_num, latest_doc_id=-1, last_limit=-1):
    url = f"{FOOLFUUKA_API_URL % archiver_url}/thread"
    payload = {"board": str(board), "num": thread_num}
    if latest_doc_id != -1:
        payload["latest_doc_id"] = int(latest_doc_id)
    if last_limit != -1:
        payload["last_limit"] = int(last_limit)

    res = await fetch_json(url, params=payload)
    if res is None:
        return None
        
    try:
        return Thread(res)
    except Exception as e:
        print(e)
        return None

async def post(archiver_url, board, post_num):
    url = f"{FOOLFUUKA_API_URL % archiver_url}/post"
    params = {"board": str(board), "num": post_num}
    res = await fetch_json(url, params=params)

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

# Cleanup when the program exits
import atexit

def cleanup():
    async def close_session():
        try:
            plebs_session = await PlebsSession.get_instance()
            await plebs_session.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    try:
        # Check if there's an event loop available
        loop = asyncio.get_event_loop()
        loop.run_until_complete(close_session())
    except RuntimeError:
        # No event loop in this thread, create a new one
        asyncio.run(close_session())
    except Exception as e:
        logger.error(f"Error during cleanup loop: {e}")

atexit.register(cleanup)
