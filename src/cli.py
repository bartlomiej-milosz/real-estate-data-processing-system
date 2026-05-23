"""Command line entry point.

Usage:
    python -m src scrape [--district SRODMIESCIE ...] [--limit XLARGE]
    python -m src clean
    python -m src export sales --output ./warsaw_all_sales.csv
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import typer

from .cleaner.batch_cleaner import BatchCleaner
from .config import settings
from .models.types import District, ListingType, ResultLimit
from .scraper.batch_scraper import BatchScraper
from .storage.repository import PropertyRepository

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

app = typer.Typer(help="Warsaw real-estate scraper and cleaner.")


def _parse_districts(values: Optional[list[str]]) -> Optional[list[District]]:
    if not values:
        return None
    return [District[v.upper()] for v in values]


def _parse_listing_types(values: Optional[list[str]]) -> Optional[list[ListingType]]:
    if not values:
        return None
    return [ListingType[v.upper()] for v in values]


@app.command()
def scrape(
    district: Optional[list[str]] = typer.Option(
        None,
        "--district",
        "-d",
        help=(
            "District name (e.g. SRODMIESCIE, MOKOTOW). Repeat for multiple. "
            "Defaults to all Warsaw districts."
        ),
    ),
    listing_type: Optional[list[str]] = typer.Option(
        None,
        "--listing-type",
        "-t",
        help="SALE or RENT. Repeat for multiple. Defaults to both.",
    ),
    limit: ResultLimit = typer.Option(
        ResultLimit.XLARGE, "--limit", help="Results per search page."
    ),
    max_properties: int = typer.Option(
        settings.max_properties_per_combination,
        "--max",
        help="Cap per district/listing-type combination.",
    ),
    delay: int = typer.Option(
        settings.delay_seconds_between_combinations,
        "--delay",
        help="Seconds to wait between district/type combinations.",
    ),
) -> None:
    """Scrape otodom and persist raw rows to the SQLite repository."""
    districts = _parse_districts(district) or list(District)
    listing_types = _parse_listing_types(listing_type) or list(ListingType)

    repository = PropertyRepository()
    batch_scraper = BatchScraper(
        repository=repository, base_output_dir=settings.raw_dir
    )

    total = asyncio.run(
        batch_scraper.scrape_multiple_combinations(
            districts=districts,
            listing_types=listing_types,
            limit=limit,
            max_properties=max_properties,
            delay_seconds=delay,
        )
    )
    logger.info(f"Scraping completed. Total properties: {total}")


@app.command()
def clean(
    listing_type: Optional[list[str]] = typer.Option(
        None,
        "--listing-type",
        "-t",
        help="SALE or RENT. Defaults to both.",
    ),
) -> None:
    """Transform raw rows into typed Property rows."""
    repository = PropertyRepository()
    batch_cleaner = BatchCleaner(repository=repository)
    listing_types = _parse_listing_types(listing_type) or list(ListingType)

    results = batch_cleaner.clean_all(listing_types)
    for lt, count in results.items():
        logger.info(f"{lt.name}: {count} cleaned rows")


@app.command()
def export(
    listing_type: str = typer.Argument(
        ..., help="SALE or RENT."
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Destination CSV path.",
    ),
) -> None:
    """Export cleaned rows to a CSV file."""
    lt = ListingType[listing_type.upper()]
    repository = PropertyRepository()
    batch_cleaner = BatchCleaner(repository=repository)
    count = batch_cleaner.export_combined_csv(lt, output)
    logger.info(f"Exported {count} rows from {lt.name} to {output}")


if __name__ == "__main__":
    app()
