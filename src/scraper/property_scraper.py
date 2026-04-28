import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from ..models.property import ScrapedListing
from .http_client import HttpClient
from .parser import parse_listing_links, parse_property_detail
from .search_params import ScrapedListingSearchQuery

logger = logging.getLogger(__name__)


class ScrapedListingScraper:
    """Orchestrates listing discovery and detail page scraping for one query."""

    def __init__(
        self,
        config: ScrapedListingSearchQuery,
        http_client: Optional[HttpClient] = None,
        max_workers: int = 5,
    ):
        self.config = config
        self.http = http_client or HttpClient()
        self.max_workers = max_workers
        self.properties: List[ScrapedListing] = []

    def get_properties(self) -> List[ScrapedListing]:
        return self.properties

    def get_properties_count(self) -> int:
        return len(self.properties)

    def scrape_multiple_pages(self, max_pages: int) -> None:
        logger.info(f"Starting scrape for {max_pages} pages")

        for page in range(1, max_pages + 1):
            logger.info(f"Processing page {page}/{max_pages}")
            page_properties = self._scrape_page(page)
            self.properties.extend(page_properties)
            logger.info(f"Page {page} done: {len(page_properties)} properties")

        logger.info(f"Finished! Total: {len(self.properties)} properties")

    def _scrape_page(self, page: int) -> List[ScrapedListing]:
        if page < 1:
            raise ValueError("Page must be 1 or greater")

        logger.info(f"Fetching page {page}")
        html = self.http.get(self.config.get_url(page=page))
        if html is None:
            return []

        links = parse_listing_links(html)
        logger.info(f"Found {len(links)} listings")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(self._scrape_detail, links))
        return [p for p in results if p is not None]

    def _scrape_detail(self, url: str) -> Optional[ScrapedListing]:
        logger.info(f"Scraping: {url}")
        html = self.http.get(url)
        if html is None:
            return None

        try:
            data = parse_property_detail(html)
            return ScrapedListing(link=url, **data)
        except ValueError as e:
            logger.error(f"Failed to build ScrapedListing for {url}: {e}")
            return None
