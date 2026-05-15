import asyncio
import logging
from typing import List

from .models.types import District, ListingType, ResultLimit
from .scraper.batch_scraper import BatchScraper
from .storage.repository import PropertyRepository

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

WARSAW_DISTRICTS: List[District] = list(District)
LISTING_TYPES: List[ListingType] = list(ListingType)
MAX_PROPERTIES: int = 500


async def main() -> None:
    logger.info("Starting property scraping...")

    repository = PropertyRepository()
    batch_scraper = BatchScraper(repository=repository)
    total_scraped = await batch_scraper.scrape_multiple_combinations(
        districts=WARSAW_DISTRICTS,
        listing_types=LISTING_TYPES,
        limit=ResultLimit.XLARGE,
        max_properties=MAX_PROPERTIES,
        delay_seconds=10,
    )

    logger.info(f"Scraping completed! Total properties: {total_scraped}")


if __name__ == "__main__":
    asyncio.run(main())
