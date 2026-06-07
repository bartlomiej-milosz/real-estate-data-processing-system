import asyncio
import logging
import math
from pathlib import Path
from typing import List

import httpx
import pandas as pd

from ..models.property import ScrapedListing
from ..models.types import District, ListingType, ResultLimit
from ..storage.repository import PropertyRepository
from .http_client import AsyncHttpClient
from .property_scraper import PropertyScraper
from .search_params import PropertySearchQuery

logger = logging.getLogger(__name__)

_LISTING_TYPE_DIRS = {
    ListingType.SALE: "sales",
    ListingType.RENT: "rents",
}


class BatchScraper:
    """Scrapes district x listing-type combinations sharing one HTTP client."""

    def __init__(
        self,
        repository: PropertyRepository | None = None,
        base_output_dir: str | Path = "./data/raw",
    ):
        self.repository = repository
        self.base_output_dir = Path(base_output_dir)

    def get_output_directory(self, listing_type: ListingType) -> Path:
        subdir = _LISTING_TYPE_DIRS.get(listing_type, listing_type.name.lower())
        return self.base_output_dir / subdir

    async def scrape_district_type(
        self,
        http: AsyncHttpClient,
        district: District,
        listing_type: ListingType,
        limit: ResultLimit,
        max_properties: int,
        skip_ids: set[str] | None = None,
    ) -> int:
        logger.info(f"Scraping {district.name} - {listing_type.name}")
        try:
            config = PropertySearchQuery(
                locations=[district],
                listing_type=listing_type,
                limit=limit,
            )
            scraper = PropertyScraper(
                config=config, http_client=http, skip_ids=skip_ids
            )
            pages_needed = math.ceil(max_properties / limit.value)
            await scraper.scrape_multiple_pages(pages_needed)

            properties = scraper.get_properties()[:max_properties]
            self._persist(properties, district, listing_type)
            return len(properties)

        except (httpx.HTTPError, ValueError, OSError) as e:
            logger.error(f"Failed {district.name} - {listing_type.name}: {e}")
            return 0

    def _persist(
        self,
        properties: List[ScrapedListing],
        district: District,
        listing_type: ListingType,
    ) -> None:
        if not properties:
            logger.warning(
                f"No properties found for {district.name} - {listing_type.name}"
            )
            return

        if self.repository is not None:
            written = self.repository.save_raw(properties, listing_type)
            logger.info(
                f"Saved {written} raw rows to repository "
                f"({district.name} - {listing_type.name})"
            )

        output_dir = self.get_output_directory(listing_type)
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{district.name.lower()}_{listing_type.name.lower()}s.csv"
        filepath = output_dir / filename
        df = pd.DataFrame([prop.model_dump() for prop in properties])
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        logger.info(f"Saved {len(properties)} properties to {filepath}")

    async def scrape_multiple_combinations(
        self,
        districts: List[District],
        listing_types: List[ListingType],
        limit: ResultLimit,
        max_properties: int,
        delay_seconds: int = 2,
        resume: bool = False,
    ) -> int:
        total_scraped = 0
        last_district, last_listing_type = districts[-1], listing_types[-1]

        skip_ids_by_type: dict[ListingType, set[str]] = {}
        if resume and self.repository is not None:
            for listing_type in listing_types:
                skip_ids_by_type[listing_type] = self.repository.existing_ids(
                    listing_type
                )
                logger.info(
                    f"Resume: {len(skip_ids_by_type[listing_type])} "
                    f"already-scraped ids for {listing_type.name}"
                )

        async with AsyncHttpClient() as http:
            for district in districts:
                for listing_type in listing_types:
                    count = await self.scrape_district_type(
                        http=http,
                        district=district,
                        listing_type=listing_type,
                        limit=limit,
                        max_properties=max_properties,
                        skip_ids=skip_ids_by_type.get(listing_type),
                    )
                    total_scraped += count

                    is_last = (
                        district == last_district and listing_type == last_listing_type
                    )
                    if not is_last:
                        logger.info(f"Waiting {delay_seconds}s before next scrape...")
                        await asyncio.sleep(delay_seconds)

        return total_scraped
