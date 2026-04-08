import logging
from pathlib import Path

import pandas as pd

from .property_cleaner import PropertyDataCleaner

logger = logging.getLogger(__name__)


class BatchCleaner:
    def __init__(
        self,
        property_cleaner: PropertyDataCleaner,
        raw_dir: str = "./data/raw",
        clean_dir: str = "./data/clean",
    ):
        self.property_cleaner = property_cleaner
        self.raw_dir = Path(raw_dir)
        self.clean_dir = Path(clean_dir)

    def clean_all_files(self) -> None:
        """Clean all CSV files in the raw directory structure"""

        if not self.raw_dir.exists():
            logger.error(f"Raw directory does not exist: {self.raw_dir}")
            return

        # Process both rents and sales directories
        for listing_type in ["rents", "sales"]:
            raw_type_dir = self.raw_dir / listing_type
            clean_type_dir = self.clean_dir / listing_type

            if not raw_type_dir.exists():
                logger.warning(f"Directory does not exist: {raw_type_dir}")
                continue

            # Get all CSV files in the directory
            csv_files = list(raw_type_dir.glob("*.csv"))

            if not csv_files:
                logger.warning(f"No CSV files found in: {raw_type_dir}")
                continue

            logger.info(f"Found {len(csv_files)} files to clean in {raw_type_dir}")

            for csv_file in csv_files:
                output_file = clean_type_dir / csv_file.name
                self.property_cleaner.clean_single_file(csv_file, output_file)

    def combine_csv_files(self, source_dir: Path, output_path: Path) -> None:
        """Combine all CSV files in source directory into one file at output path"""

        cleaned_csv_files = list(source_dir.glob("*.csv"))

        if not cleaned_csv_files:
            logger.warning(f"No CSV files found in {source_dir}")
            return

        combined_dfs = []

        for csv_file in cleaned_csv_files:
            try:
                df = pd.read_csv(csv_file)
                combined_dfs.append(df)
                logger.info(f"Added {len(df)} rows from {csv_file.name}")
            except (OSError, pd.errors.ParserError) as e:
                logger.error(f"Failed to read {csv_file}: {e}")

        if combined_dfs:
            final_df = pd.concat(combined_dfs, ignore_index=True)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            final_df.to_csv(output_path, index=False, encoding="utf-8-sig")
            logger.info(f"Combined {len(final_df)} rows into {output_path}")
