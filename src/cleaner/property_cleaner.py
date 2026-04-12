import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

_INT_COLUMNS = (
    "price",
    "rooms",
    "maintenance_fee",
    "year_built",
    "current_floor",
    "total_floors",
)
_SECURITY_FEATURES = {
    "gated_area": "teren zamknięty",
    "monitoring": "monitoring",
    "security_guard": "ochrona",
}
_ADDITIONAL_FEATURES = {
    "balcony": "balkon",
    "parking": "garaż/miejsce parkingowe",
    "terrace": "taras",
    "garden": "ogródek",
    "basement": "piwnica",
    "utility_rooms": "pom. użytkowe",
    "non_smokers_only": "tylko dla niepalących",
    "students_allowed": "wynajmę również studentom",
    "separate_kitchen": "oddzielna kuchnia",
}


class PropertyDataCleaner:
    """Vectorised pandas pipeline turning raw scraped strings into typed columns."""

    def _digits_to_int(self, series: pd.Series) -> pd.Series:
        return (
            series.astype("string")
            .str.replace(r"[^\d]", "", regex=True)
            .replace("", pd.NA)
            .astype("Int64")
        )

    def _first_int(self, series: pd.Series) -> pd.Series:
        return (
            series.astype("string")
            .str.extract(r"(\d+)", expand=False)
            .astype("Int64")
        )

    def _first_float(self, series: pd.Series) -> pd.Series:
        return (
            series.astype("string")
            .str.extract(r"(\d+(?:\.\d+)?)", expand=False)
            .astype("Float64")
        )

    def _year_built(self, series: pd.Series) -> pd.Series:
        return (
            series.astype("string")
            .str.extract(r"((?:19|20)\d{2})", expand=False)
            .astype("Int64")
        )

    def _elevator(self, series: pd.Series) -> pd.Series:
        lowered = series.astype("string").str.lower().str.strip()
        return lowered.map({"tak": True, "nie": False}).astype("boolean")

    def _split_location(self, series: pd.Series) -> pd.DataFrame:
        parts = series.astype("string").str.split(", ", expand=True)
        result = pd.DataFrame(
            {"district": pd.NA, "neighborhood": pd.NA, "street": pd.NA},
            index=series.index,
            dtype="string",
        )

        four = parts.notna().sum(axis=1) == 4
        five = parts.notna().sum(axis=1) == 5

        if four.any():
            result.loc[four, "neighborhood"] = parts.loc[four, 0]
            result.loc[four, "district"] = parts.loc[four, 1]
        if five.any():
            result.loc[five, "street"] = parts.loc[five, 0]
            result.loc[five, "neighborhood"] = parts.loc[five, 1]
            result.loc[five, "district"] = parts.loc[five, 2]

        return result

    def _split_floor(self, series: pd.Series) -> pd.DataFrame:
        as_str = series.astype("string").str.strip()
        parts = as_str.str.split("/", n=1, expand=True)
        current = parts[0].str.strip().replace({"parter": "0"})
        if parts.shape[1] > 1:
            total = parts[1].str.strip()
        else:
            total = pd.Series(pd.NA, index=series.index)

        to_int = lambda s: pd.to_numeric(s, errors="coerce").astype("Int64")  # noqa: E731
        return pd.DataFrame(
            {"current_floor": to_int(current), "total_floors": to_int(total)}
        )

    def _flags_from_text(
        self, series: pd.Series, mapping: dict[str, str]
    ) -> pd.DataFrame:
        lowered = series.astype("string").str.lower().str.strip()
        present = lowered.notna()
        result = pd.DataFrame(
            {column: pd.NA for column in mapping},
            index=series.index,
            dtype="boolean",
        )
        for column, needle in mapping.items():
            result.loc[present, column] = lowered.loc[present].str.contains(
                needle, regex=False, na=False
            )
        return result

    def clean_single_file(self, input_path: Path, output_path: Path) -> None:
        try:
            logger.info(f"Cleaning: {input_path}")
            df = pd.read_csv(input_path)

            df["price"] = self._digits_to_int(df["price"])
            df["area"] = self._first_float(df["area"])
            df["rooms"] = self._first_int(df["rooms"])
            df["maintenance_fee"] = self._first_int(df["maintenance_fee"])
            df["year_built"] = self._year_built(df["year_built"])
            df["elevator"] = self._elevator(df["elevator"])

            df = pd.concat([df, self._split_location(df["location"])], axis=1)
            df = pd.concat([df, self._split_floor(df["floor"])], axis=1)
            df = pd.concat(
                [df, self._flags_from_text(df["security"], _SECURITY_FEATURES)],
                axis=1,
            )
            df = pd.concat(
                [
                    df,
                    self._flags_from_text(
                        df["additional_features"], _ADDITIONAL_FEATURES
                    ),
                ],
                axis=1,
            )

            df = df.drop(
                columns=[
                    "link",
                    "location",
                    "floor",
                    "security",
                    "additional_features",
                ],
                errors="ignore",
            )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False, encoding="utf-8-sig")

            logger.info(f"Cleaned and saved: {output_path}")
            logger.info(f"Properties processed: {len(df)}")

        except (OSError, pd.errors.ParserError, KeyError) as e:
            logger.error(f"Failed to clean {input_path}: {e}")
