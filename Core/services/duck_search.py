import asyncio
from playwright.async_api import async_playwright, TimeoutError

from Core.utils.utils import best_match

class CrawlerDuckDuckGo:
    """
    An asynchronous crawler for DuckDuckGo that initializes one browser page
    and reuses it for all subsequent searches for maximum efficiency.

    ### Usage:
        #### Instantiate object with:
        crawler = await CrawlerDuckDuckGo.create(headless=False)
        #### Delete object with:
        await crawler.close()

    ### Methods:
        #### search_product()
        #### close()

    """
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def _start(self, headless=True):
        print("Starting Playwright and initializing a reusable browser page...", end='')
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        )
        self.page = await self.context.new_page()
        print("Reusable page is ready.\n")

    @classmethod
    async def create(cls, headless=True):
        """
        Asynchronously creates and fully initializes the crawler instance.
        """
        crawler = cls()
        await crawler._start(headless=headless)
        return crawler

    async def search_product(self, product_name: str, max_results: int=10):
        """
        Parameters:
            product_name: The string that will be queried on duckduckgo
            max_results: Number of results to be returned if found
        """
        urls = []
        
        print(f"Searching for '{product_name}' ...")
        try:
            await self.page.goto("https://duckduckgo.com/", timeout=15000)
            await self.page.fill("input[name='q']", product_name)
            await self.page.keyboard.press("Enter")
            await self.page.wait_for_selector("a[data-testid='result-title-a']", timeout=60000)

            results = await self.page.query_selector_all("a[data-testid='result-title-a']")
            for r in results:
                href = await r.get_attribute("href")
                if href and href.startswith("http"):
                    urls.append(href)
                if len(urls) >= max_results:
                    break
        except TimeoutError:
            print(f"Could not find results for '{product_name}' or the page did not load.")
        
        print(f"Found {len(urls)} results.")

        return best_match(urls)
    
    async def close(self):
        print("Closing reusable page, context, and browser...")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("Crawler cleanup complete.")


async def main():
    print("--- Starting efficient async crawler ---")
    
    crawler = await CrawlerDuckDuckGo.create(headless=False)
    
    item = input("Enter what to search on DuckDuckGo: ")
    linkuri = await crawler.search_product(item, max_results=10)
    print(f"\nLinks for {item}:\n{linkuri}")
    
    await crawler.close()
if __name__ == "__main__":
    asyncio.run(main())
