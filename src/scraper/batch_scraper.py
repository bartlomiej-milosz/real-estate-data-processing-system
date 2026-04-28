import logging
import math
import time
from pathlib import Path
from typing import List

import pandas as pd
import requests

from ..models.property import ScrapedListing
from ..models.types import District, ListingType, ResultLimit
from .property_scraper import ScrapedListingScraper
from .search_params import ScrapedListingSearchQuery

logger = logging.getLogger(__name__)

_LISTING_TYPE_DIRS = {
    ListingType.SALE: "sales",
    ListingType.RENT: "rents",
}


class BatchScraper:
    """Handles batch scraping operations for multiple districts and listing types"""

    def __init__(self, base_output_dir: str | Path = "./data/raw"):
        self.base_output_dir = Path(base_output_dir)

    def get_output_directory(self, listing_type: ListingType) -> Path:
        subdir = _LISTING_TYPE_DIRS.get(listing_type, listing_type.name.lower())
        return self.base_output_dir / subdir

    def scrape_district_type(
        self,
        district: District,
        listing_type: ListingType,
        limit: ResultLimit,
        max_properties: int,
    ) -> int:
        """Scrape one district-property type combination"""

        logger.info(f"Scraping {district.name} - {listing_type.name}")

        try:
            config = ScrapedListingSearchQuery(
                locations=[district],
                listing_type=listing_type,
                limit=limit,
            )

            scraper = ScrapedListingScraper(config=config)
            pages_needed = math.ceil(max_properties / limit.value)
            scraper.scrape_multiple_pages(pages_needed)

            properties: List[ScrapedListing] = scraper.get_properties()[:max_properties]

            self._save_properties(properties, district, listing_type)

            return len(properties)

        except (requests.RequestException, ValueError, OSError) as e:
            logger.error(f"Failed {district.name} - {listing_type.name}: {e}")
            return 0

    def _save_properties(
        self,
        properties: List[ScrapedListing],
        district: District,
        listing_type: ListingType,
    ) -> None:
        """Save properties to CSV file"""

        output_dir = self.get_output_directory(listing_type)
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{district.name.lower()}_{listing_type.name.lower()}s.csv"
        filepath = output_dir / filename

        if properties:
            df = pd.DataFrame([prop.model_dump() for prop in properties])
            df.to_csv(filepath, index=False, encoding="utf-8-sig")
            logger.info(f"Saved {len(properties)} properties to {filepath}")
        else:
            logger.warning(
                f"No properties found for {district.name} - {listing_type.name}"
            )

    def scrape_multiple_combinations(
        self,
        districts: List[District],
        listing_types: List[ListingType],
        limit: ResultLimit,
        max_properties: int,
        delay_seconds: int = 2,
    ) -> int:
        """Scrape multiple district-property listing type combinations"""
        total_scraped = 0

        last_district = districts[-1]
        last_listing_type = listing_types[-1]

        for district in districts:
            for listing_type in listing_types:
                count = self.scrape_district_type(
                    district=district,
                    listing_type=listing_type,
                    limit=limit,
                    max_properties=max_properties,
                )
                total_scraped += count

                is_last = (
                    district == last_district and listing_type == last_listing_type
                )
                if not is_last:
                    logger.info(
                        f"Waiting {delay_seconds} seconds before next scrape..."
                    )
                    time.sleep(delay_seconds)

        return total_scraped
