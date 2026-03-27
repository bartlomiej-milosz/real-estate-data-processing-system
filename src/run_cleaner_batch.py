import logging
from pathlib import Path

from .cleaner.batch_cleaner import BatchCleaner
from .cleaner.property_cleaner import PropertyDataCleaner

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """Main function to run the data cleaning process"""

    logger.info("Starting property data cleaning...")

    property_cleaner = PropertyDataCleaner()
    batch_cleaner = BatchCleaner(
        property_cleaner=property_cleaner,
        raw_dir="./data/raw",
        clean_dir="./data/clean",
    )

    batch_cleaner.clean_all_files()

    logger.info("Data cleaning completed!")
    logger.info("Check ./data/clean/rents/ and ./data/clean/sales/ for results")

    clean_rents_dir = Path("./data/clean/rents")
    clean_sales_dir = Path("./data/clean/sales")
    combined_output_dir = Path("./data/clean/combined")
    combined_output_dir.mkdir(parents=True, exist_ok=True)

    batch_cleaner.combine_csv_files(
        clean_rents_dir, combined_output_dir / "warsaw_all_rents.csv"
    )
    batch_cleaner.combine_csv_files(
        clean_sales_dir, combined_output_dir / "warsaw_all_sales.csv"
    )


if __name__ == "__main__":
    main()
