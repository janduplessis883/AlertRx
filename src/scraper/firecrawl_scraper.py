import os
from firecrawl import FirecrawlApp

class FirecrawlScraper:
    def __init__(self, api_key=None):
        if api_key is None:
            api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise ValueError("Firecrawl API key not provided. Set FIRECRAWL_API_KEY environment variable or pass it to the constructor.")
        self.app = FirecrawlApp(api_key=api_key)

    def scrape_page(self, url):
        """
        Scrapes a single URL using Firecrawl and returns structured JSON.
        """
        try:
            # You can customize the Firecrawl scrape options here
            # For example, to extract markdown:
            # result = self.app.scrape_url(url, {'pageOptions': {'onlyMainContent': True}})
            # Or to extract structured data:
            result = self.app.scrape_url(url, {'pageOptions': {'extractJson': True}})
            return result
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None

    def crawl_site(self, url):
        """
        Crawls an entire site using Firecrawl and returns structured JSON for each page.
        """
        try:
            # You can customize the Firecrawl crawl options here
            # For example, to limit depth or include/exclude patterns:
            # result = self.app.crawl_url(url, {'crawlerOptions': {'depth': 1}})
            result = self.app.crawl_url(url)
            return result
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None

if __name__ == "__main__":
    # Example usage (requires FIRECRAWL_API_KEY environment variable set)
    # scraper = FirecrawlScraper()
    # example_url = "https://www.gov.uk/drug-safety-update" # Example medical alert source
    # print(f"Scraping single page: {example_url}")
    # data = scraper.scrape_page(example_url)
    # if data:
    #     print(data)

    # print(f"\nCrawling site: {example_url}")
    # crawled_data = scraper.crawl_site(example_url)
    # if crawled_data:
    #     for item in crawled_data:
    #         print(item)
    pass
