"""Unit tests for the vectorised PropertyDataCleaner."""

import pandas as pd
import pytest

from src.cleaner.property_cleaner import PropertyDataCleaner
from src.models.property import Property


@pytest.fixture
def cleaner() -> PropertyDataCleaner:
    return PropertyDataCleaner()


def _series(values) -> pd.Series:
    return pd.Series(values, dtype="object")


def test_digits_to_int_strips_currency_and_separators(cleaner):
    result = cleaner._digits_to_int(_series(["9 600 000 zł", "850zł", None, ""]))
    assert result.tolist()[:2] == [9_600_000, 850]
    assert result.isna().tolist()[2:] == [True, True]


def test_first_int_extracts_leading_number(cleaner):
    result = cleaner._first_int(_series(["3 pokoje", "12", "", None]))
    assert result.tolist()[:2] == [3, 12]
    assert result.isna().tolist()[2:] == [True, True]


def test_first_float_handles_decimal(cleaner):
    result = cleaner._first_float(_series(["48.07 m²", "100", None]))
    assert result.tolist()[:2] == [48.07, 100.0]
    assert result.isna().tolist()[2:] == [True]


def test_year_built_only_accepts_19xx_20xx(cleaner):
    result = cleaner._year_built(_series(["1939", "rok 2017", "1850", None]))
    values = result.tolist()
    assert values[0] == 1939
    assert values[1] == 2017
    assert result.isna().tolist()[2:] == [True, True]


def test_elevator_maps_polish_yes_no(cleaner):
    result = cleaner._elevator(_series(["tak", "Nie", "brak danych", None]))
    assert result.tolist()[:2] == [True, False]
    assert result.isna().tolist()[2:] == [True, True]


def test_split_floor_handles_parter_and_pair(cleaner):
    result = cleaner._split_floor(_series(["3/5", "parter", "10", None]))
    assert result["current_floor"].tolist()[:3] == [3, 0, 10]
    assert result["total_floors"].tolist()[:1] == [5]
    assert result["total_floors"].isna().tolist()[1:] == [True, True, True]
    assert result["current_floor"].isna().tolist()[3:] == [True]


def test_split_location_four_parts_drops_street(cleaner):
    location = "Śródmieście Północne, Śródmieście, Warszawa, mazowieckie"
    result = cleaner._split_location(_series([location]))
    assert result.loc[0, "neighborhood"] == "Śródmieście Północne"
    assert result.loc[0, "district"] == "Śródmieście"
    assert pd.isna(result.loc[0, "street"])


def test_split_location_five_parts_includes_street(cleaner):
    location = "ul. Grzybowska, Solec, Śródmieście, Warszawa, mazowieckie"
    result = cleaner._split_location(_series([location]))
    assert result.loc[0, "street"] == "ul. Grzybowska"
    assert result.loc[0, "neighborhood"] == "Solec"
    assert result.loc[0, "district"] == "Śródmieście"


def test_split_location_handles_na(cleaner):
    result = cleaner._split_location(_series([None]))
    assert pd.isna(result.loc[0, "district"])
    assert pd.isna(result.loc[0, "neighborhood"])
    assert pd.isna(result.loc[0, "street"])


def test_flags_from_text_detects_substrings(cleaner):
    mapping = {"balcony": "balkon", "garden": "ogródek"}
    series = _series(["balkon | piwnica", "ogródek", "monitoring", None])
    result = cleaner._flags_from_text(series, mapping)
    assert result["balcony"].tolist()[:3] == [True, False, False]
    assert result["garden"].tolist()[:3] == [False, True, False]
    # NA row stays NA
    assert result["balcony"].isna().tolist()[3:] == [True]


def test_clean_to_models_produces_property_instances(cleaner):
    raw = pd.DataFrame(
        [
            {
                "id": "IDabc",
                "link": "https://www.otodom.pl/pl/oferta/foo-IDabc",
                "price": "9 600 000 zł",
                "location": "ul. Grzybowska, Solec, Śródmieście, Warszawa, mazowieckie",
                "area": "48.07 m²",
                "rooms": "3 pokoje",
                "heating": "miejskie",
                "floor": "5/10",
                "maintenance_fee": "850 zł",
                "condition": "do zamieszkania",
                "market": "wtórny",
                "ownership": "pełna własność",
                "advertiser_type": "prywatny",
                "year_built": "1939",
                "elevator": "tak",
                "building_type": "kamienica",
                "windows": "plastikowe",
                "security": "teren zamknięty | monitoring",
                "additional_features": "balkon | piwnica | taras",
            }
        ]
    )

    properties = cleaner.clean_to_models(raw)
    assert len(properties) == 1
    prop = properties[0]
    assert isinstance(prop, Property)
    assert prop.id == "IDabc"
    assert prop.price == 9_600_000
    assert prop.area == pytest.approx(48.07)
    assert prop.rooms == 3
    assert prop.maintenance_fee == 850
    assert prop.year_built == 1939
    assert prop.elevator is True
    assert prop.current_floor == 5
    assert prop.total_floors == 10
    assert prop.district == "Śródmieście"
    assert prop.neighborhood == "Solec"
    assert prop.street == "ul. Grzybowska"
    assert prop.gated_area is True
    assert prop.monitoring is True
    assert prop.security_guard is False
    assert prop.balcony is True
    assert prop.terrace is True
    assert prop.parking is False


def test_clean_to_models_preserves_none_for_missing_fields(cleaner):
    raw = pd.DataFrame(
        [
            {
                "id": "IDxyz",
                "link": "https://www.otodom.pl/pl/oferta/x-IDxyz",
                "price": None,
                "location": None,
                "area": None,
                "rooms": None,
                "heating": None,
                "floor": None,
                "maintenance_fee": None,
                "condition": None,
                "market": None,
                "ownership": None,
                "advertiser_type": None,
                "year_built": None,
                "elevator": None,
                "building_type": None,
                "windows": None,
                "security": None,
                "additional_features": None,
            }
        ]
    )
    prop = cleaner.clean_to_models(raw)[0]
    assert prop.price is None
    assert prop.area is None
    assert prop.elevator is None
    assert prop.district is None
    assert prop.balcony is None
