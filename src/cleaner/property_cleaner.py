import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class PropertyDataCleaner:
    def __init__(self):
        pd.set_option("display.max_colwidth", None)

    def _clean_price(self, price) -> Optional[int]:
        """Clean price data - remove any non-numeric characters except digits"""
        if pd.isna(price):
            return pd.NA

        # Convert to string and extract only digits
        price_str = str(price)
        price_numbers = re.sub(r"[^\d]", "", price_str)

        if price_numbers:
            return int(price_numbers)
        return pd.NA

    def _clean_maintenance_fee(self, fee) -> Optional[int]:
        """Extract numeric maintenance fee"""
        if pd.isna(fee):
            return np.nan

        # Extract numbers from maintenance fee
        match = re.search(r"\d+", str(fee))
        if match:
            return int(match.group(0))
        return np.nan

    def _clean_area(self, area) -> Optional[float]:
        if pd.isna(area):
            return np.nan

        match = re.search(r"\d+(?:\.\d+)?", str(area))
        if match:
            return float(match.group(0))
        return np.nan

    def _clean_rooms(self, rooms) -> Optional[int]:
        """Extract number of rooms"""
        if pd.isna(rooms):
            return pd.NA

        match = re.search(r"\d+", str(rooms))
        if match:
            return int(match.group(0))
        return pd.NA

    def _clean_year_built(self, year) -> Optional[int]:
        """Extract year built"""
        if pd.isna(year):
            return pd.NA

        match = re.search(r"\b(19|20)\d{2}\b", str(year))
        if match:
            return int(match.group(0))
        return pd.NA

    def _split_location(self, location) -> Dict[str, Optional[str]]:
        if pd.isna(location):
            return {"district": pd.NA, "neighborhood": pd.NA, "street": pd.NA}

        parts: List[str] = location.split(", ")
        if len(parts) == 4:
            district = parts[1]
            neighborhood = parts[0]
            street = pd.NA
        elif len(parts) == 5:
            district = parts[2]
            neighborhood = parts[1]
            street = parts[0]
        else:
            district = pd.NA
            neighborhood = pd.NA
            street = pd.NA

        return {"district": district, "neighborhood": neighborhood, "street": street}

    def _split_floor(self, floor) -> Dict[str, Optional[int]]:
        if pd.isna(floor):
            return {"current_floor": pd.NA, "total_floors": pd.NA}

        if "/" in str(floor):
            parts: List[str] = floor.split("/")
            current: str = parts[0].strip()
            total: Optional[str] = parts[1].strip() if len(parts) > 1 else pd.NA
        else:
            current: str = str(floor).strip()
            total = pd.NA

        # Convert "parter" to 0 (ground floor)
        if current == "parter":
            current = "0"

        # Handle non-numeric values
        def safe_int(value):
            if value is pd.NA:
                return pd.NA
            try:
                return int(value)
            except ValueError:
                return pd.NA

        return {"current_floor": safe_int(current), "total_floors": safe_int(total)}

    def _clean_elevator(self, is_elevator) -> Optional[bool]:
        if pd.isna(is_elevator):
            return pd.NA

        elevator_str: str = str(is_elevator).lower().strip()
        if elevator_str == "tak":
            return True
        elif elevator_str == "nie":
            return False
        else:
            return pd.Na

    def _extract_security_features(
        self, security_features
    ) -> Dict[str, Optional[bool]]:
        if pd.isna(security_features):
            return {"gated_area": pd.NA, "monitoring": pd.NA, "security_guard": pd.NA}

        security_features_str: str = str(security_features).lower().strip()
        return {
            "gated_area": "teren zamknięty" in security_features_str,
            "monitoring": "monitoring" in security_features_str,
            "security_guard": "ochrona" in security_features_str,
        }

    def _extract_additional_features(
        self, additional_features
    ) -> Dict[str, Optional[bool]]:
        if pd.isna(additional_features):
            return {
                "balcony": pd.NA,
                "parking": pd.NA,
                "terrace": pd.NA,
                "garden": pd.NA,
                "basement": pd.NA,
                "utility_rooms": pd.NA,
                "non_smokers_only": pd.NA,
                "students_allowed": pd.NA,
                "separate_kitchen": pd.NA,
            }

        features_str: str = str(additional_features).lower().strip()

        return {
            "balcony": "balkon" in features_str,
            "parking": "garaż/miejsce parkingowe" in features_str,
            "terrace": "taras" in features_str,
            "garden": "ogródek" in features_str,
            "basement": "piwnica" in features_str,
            "utility_rooms": "pom. użytkowe" in features_str,
            "non_smokers_only": "tylko dla niepalących" in features_str,
            "students_allowed": "wynajmę również studentom" in features_str,
            "separate_kitchen": "oddzielna kuchnia" in features_str,
        }

    def clean_single_file(self, input_path: Path, output_path: Path) -> None:
        """Clean a single CSV file"""

        try:
            logger.info(f"Cleaning: {input_path}")
            df = pd.read_csv(input_path)

            # Apply cleaning functions
            df["price"] = df["price"].apply(self._clean_price)
            df["area"] = df["area"].apply(self._clean_area)
            df["rooms"] = df["rooms"].apply(self._clean_rooms)
            df["maintenance_fee"] = df["maintenance_fee"].apply(
                self._clean_maintenance_fee
            )
            df["year_built"] = df["year_built"].apply(self._clean_year_built)
            df["elevator"] = df["elevator"].apply(self._clean_elevator)

            # Split location into separate columns
            location_split = df["location"].apply(self._split_location)
            location_df = pd.DataFrame(location_split.to_list())
            df = pd.concat([df, location_df], axis=1)

            # Split floor information
            floor_split = df["floor"].apply(self._split_floor)
            floor_df = pd.DataFrame(floor_split.to_list())
            df = pd.concat([df, floor_df], axis=1)

            # Extract security features
            security_features = df["security"].apply(self._extract_security_features)
            security_df = pd.DataFrame(security_features.to_list())
            df = pd.concat([df, security_df], axis=1)

            # Extract additional features
            additional_features_data = df["additional_features"].apply(
                self._extract_additional_features
            )
            additional_features_df = pd.DataFrame(additional_features_data.to_list())
            df = pd.concat([df, additional_features_df], axis=1)

            # Drop original columns that were split
            columns_to_drop = [
                "link",
                "location",
                "floor",
                "security",
                "additional_features",
            ]
            existing_columns_to_drop = [
                col for col in columns_to_drop if col in df.columns
            ]
            df = df.drop(existing_columns_to_drop, axis=1)

            # Adjust data types - do this AFTER all cleaning
            type_conversions = {}

            if "price" in df.columns:
                type_conversions["price"] = "Int64"
            if "rooms" in df.columns:
                type_conversions["rooms"] = "Int64"
            if "maintenance_fee" in df.columns:
                type_conversions["maintenance_fee"] = "Int64"
            if "year_built" in df.columns:
                type_conversions["year_built"] = "Int64"
            if "current_floor" in df.columns:
                type_conversions["current_floor"] = "Int64"
            if "total_floors" in df.columns:
                type_conversions["total_floors"] = "Int64"
            if "elevator" in df.columns:
                type_conversions["elevator"] = "boolean"

            # Apply type conversions
            df = df.astype(type_conversions)

            # Save cleaned data
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False, encoding="utf-8-sig")

            logger.info(f"Cleaned and saved: {output_path}")
            logger.info(f"Properties processed: {len(df)}")

        except Exception as e:
            logger.error(f"Failed to clean {input_path}: {e}")
