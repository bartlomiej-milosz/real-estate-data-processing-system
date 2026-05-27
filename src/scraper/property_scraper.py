import asyncio
import logging
from typing import List, Optional

from ..models.property import ScrapedListing, extract_listing_id
from .http_client import AsyncHttpClient
from .parser import parse_listing_links, parse_property_detail
from .search_params import PropertySearchQuery

logger = logging.getLogger(__name__)


class PropertyScraper:
    """Async orchestrator: discovers listings, fetches detail pages concurrently."""

    def __init__(
        self,
        config: PropertySearchQuery,
        http_client: Optional[AsyncHttpClient] = None,
        skip_ids: Optional[set[str]] = None,
    ):
        self.config = config
        self.http = http_client or AsyncHttpClient()
        self._owns_client = http_client is None
        self.skip_ids: set[str] = skip_ids or set()
        self.properties: List[ScrapedListing] = []

    def get_properties(self) -> List[ScrapedListing]:
        return self.properties

    def get_properties_count(self) -> int:
        return len(self.properties)

    async def scrape_multiple_pages(self, max_pages: int) -> None:
        logger.info(f"Starting scrape for {max_pages} pages")
        try:
            for page in range(1, max_pages + 1):
                logger.info(f"Processing page {page}/{max_pages}")
                page_properties = await self._scrape_page(page)
                self.properties.extend(page_properties)
                logger.info(f"Page {page} done: {len(page_properties)} properties")
            logger.info(f"Finished! Total: {len(self.properties)} properties")
        finally:
            if self._owns_client:
                await self.http.close()

    async def _scrape_page(self, page: int) -> List[ScrapedListing]:
        if page < 1:
            raise ValueError("Page must be 1 or greater")

        logger.info(f"Fetching page {page}")
        html = await self.http.get(self.config.get_url(page=page))
        if html is None:
            return []

        links = parse_listing_links(html)
        logger.info(f"Found {len(links)} listings")

        if self.skip_ids:
            before = len(links)
            links = [
                url for url in links if extract_listing_id(url) not in self.skip_ids
            ]
            skipped = before - len(links)
            if skipped:
                logger.info(f"Skipping {skipped} listings already in repository")

        results = await asyncio.gather(*(self._scrape_detail(url) for url in links))
        return [p for p in results if p is not None]

    async def _scrape_detail(self, url: str) -> Optional[ScrapedListing]:
        logger.info(f"Scraping: {url}")
        html = await self.http.get(url)
        if html is None:
            return None

        try:
            data = parse_property_detail(html)
            return ScrapedListing(link=url, **data)
        except ValueError as e:
            logger.error(f"Failed to build ScrapedListing for {url}: {e}")
            return None
