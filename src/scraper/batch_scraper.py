import logging
import os
from typing import List

import pandas as pd

from ..models.property import Property
from ..models.types import District, ListingType, ResultLimit
from .property_scraper import PropertyScraper
from .search_params import PropertySearchQuery

logger = logging.getLogger(__name__)


class BatchScraper:
    """Handles batch scraping operations for multiple districts and listing types"""

    def __init__(self, base_output_dir: str = "./data/raw"):
        self.base_output_dir = base_output_dir

    def get_output_directory(self, listing_type: ListingType) -> str:
        """Get output directory based on listing type"""

        if listing_type == ListingType.SALE:
            return os.path.join(self.base_output_dir, "sales")
        elif listing_type == ListingType.RENT:
            return os.path.join(self.base_output_dir, "rents")
        else:
            return os.path.join(self.base_output_dir, listing_type.name.lower())

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
            config = PropertySearchQuery(
                locations=[district],
                listing_type=listing_type,
                limit=limit,
            )

            scraper = PropertyScraper(config=config)
            pages_needed: int = int((max_properties / limit.value) + 1)
            scraper.scrape_multiple_pages(pages_needed)

            properties: List[Property] = scraper.get_properties()[:max_properties]

            self._save_properties(properties, district, listing_type)

            return len(properties)

        except Exception as e:
            logger.error(f"Failed {district.name} - {listing_type.name}: {e}")
            return 0

    def _save_properties(
        self,
        properties: List[Property],
        district: District,
        listing_type: ListingType,
    ) -> None:
        """Save properties to CSV file"""

        output_dir = self.get_output_directory(listing_type)
        os.makedirs(output_dir, exist_ok=True)

        filename = f"{district.name.lower()}_{listing_type.name.lower()}{'s'}.csv"
        filepath = os.path.join(output_dir, filename)

        if properties:
            df = pd.DataFrame([prop.__dict__ for prop in properties])
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
        import time

        total_scraped = 0

        for district in districts:
            for listing_type in listing_types:
                count = self.scrape_district_type(
                    district=district,
                    listing_type=listing_type,
                    limit=limit,
                    max_properties=max_properties,
                )
                total_scraped += count

                if not (
                    district == districts[-1] and listing_type == listing_types[-1]
                ):
                    logger.info(
                        f"Waiting {delay_seconds} seconds before next scrape..."
                    )
                    time.sleep(delay_seconds)

        return total_scraped
