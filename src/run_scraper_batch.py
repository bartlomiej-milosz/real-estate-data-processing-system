import asyncio
import logging
from typing import List

from .config import settings
from .models.types import District, ListingType, ResultLimit
from .scraper.batch_scraper import BatchScraper
from .storage.repository import PropertyRepository

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

WARSAW_DISTRICTS: List[District] = list(District)
LISTING_TYPES: List[ListingType] = list(ListingType)


async def main() -> None:
    logger.info("Starting property scraping...")

    repository = PropertyRepository()
    batch_scraper = BatchScraper(
        repository=repository, base_output_dir=settings.raw_dir
    )
    total_scraped = await batch_scraper.scrape_multiple_combinations(
        districts=WARSAW_DISTRICTS,
        listing_types=LISTING_TYPES,
        limit=ResultLimit.XLARGE,
        max_properties=settings.max_properties_per_combination,
        delay_seconds=settings.delay_seconds_between_combinations,
    )

    logger.info(f"Scraping completed! Total properties: {total_scraped}")


if __name__ == "__main__":
    asyncio.run(main())
