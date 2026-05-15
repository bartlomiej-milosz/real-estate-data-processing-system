import logging
from pathlib import Path

from .cleaner.batch_cleaner import BatchCleaner
from .models.types import ListingType
from .storage.repository import PropertyRepository

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting property data cleaning...")

    repository = PropertyRepository()
    batch_cleaner = BatchCleaner(repository=repository)
    results = batch_cleaner.clean_all()

    for listing_type, count in results.items():
        logger.info(f"{listing_type.name}: {count} cleaned rows")

    combined_dir = Path("./data/clean/combined")
    batch_cleaner.export_combined_csv(
        ListingType.RENT, combined_dir / "warsaw_all_rents.csv"
    )
    batch_cleaner.export_combined_csv(
        ListingType.SALE, combined_dir / "warsaw_all_sales.csv"
    )


if __name__ == "__main__":
    main()
