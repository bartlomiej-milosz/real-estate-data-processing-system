import asyncio
import logging
from typing import List

from .models.types import District, ListingType, ResultLimit
from .scraper.batch_scraper import BatchScraper

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

WARSAW_DISTRICTS: List[District] = list(District)
LISTING_TYPES: List[ListingType] = list(ListingType)
MAX_PROPERTIES: int = 500


async def main() -> None:
    logger.info("Starting property scraping...")

    batch_scraper = BatchScraper()
    total_scraped = await batch_scraper.scrape_multiple_combinations(
        districts=WARSAW_DISTRICTS,
        listing_types=LISTING_TYPES,
        limit=ResultLimit.XLARGE,
        max_properties=MAX_PROPERTIES,
        delay_seconds=10,
    )

    logger.info(f"Scraping completed! Total properties: {total_scraped}")
    logger.info("Check ./data/raw/sales/ and ./data/raw/rents/ for results")


if __name__ == "__main__":
    asyncio.run(main())
