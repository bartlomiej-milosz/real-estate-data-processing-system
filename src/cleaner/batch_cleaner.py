"""Orchestrates cleaning across listing types using the SQLite repository."""

import logging
from pathlib import Path
from typing import Iterable

import pandas as pd

from ..models.types import ListingType
from ..storage.repository import PropertyRepository
from .property_cleaner import PropertyDataCleaner

logger = logging.getLogger(__name__)


class BatchCleaner:
    def __init__(
        self,
        repository: PropertyRepository,
        property_cleaner: PropertyDataCleaner | None = None,
    ):
        self.repository = repository
        self.property_cleaner = property_cleaner or PropertyDataCleaner()

    def clean_all(
        self, listing_types: Iterable[ListingType] = tuple(ListingType)
    ) -> dict[ListingType, int]:
        results: dict[ListingType, int] = {}
        for listing_type in listing_types:
            raw = self.repository.load_raw(listing_type)
            if raw.empty:
                logger.warning(f"No raw rows for {listing_type.name}")
                results[listing_type] = 0
                continue

            logger.info(f"Cleaning {len(raw)} rows for {listing_type.name}")
            properties = self.property_cleaner.clean_to_models(raw)
            written = self.repository.save_cleaned(properties, listing_type)
            results[listing_type] = written
            logger.info(f"Saved {written} cleaned rows for {listing_type.name}")
        return results

    def export_combined_csv(
        self, listing_type: ListingType, output_path: Path
    ) -> int:
        df = self.repository.load_cleaned(listing_type)
        if df.empty:
            logger.warning(f"No cleaned rows for {listing_type.name}")
            return 0

        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        logger.info(f"Exported {len(df)} rows to {output_path}")
        return len(df)

    @staticmethod
    def concat_csv_files(source_dir: Path, output_path: Path) -> int:
        """Legacy helper: concatenate per-district CSVs into one file."""
        csv_files = list(source_dir.glob("*.csv"))
        if not csv_files:
            logger.warning(f"No CSV files found in {source_dir}")
            return 0

        dfs = []
        for csv_file in csv_files:
            try:
                dfs.append(pd.read_csv(csv_file))
            except (OSError, pd.errors.ParserError) as e:
                logger.error(f"Failed to read {csv_file}: {e}")

        if not dfs:
            return 0

        combined = pd.concat(dfs, ignore_index=True)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined.to_csv(output_path, index=False, encoding="utf-8-sig")
        logger.info(f"Combined {len(combined)} rows into {output_path}")
        return len(combined)
