"""Tests for the SQLite-backed PropertyRepository.

Uses a temporary file-based SQLite DB so we exercise the real engine and
upsert semantics rather than mocking SQLAlchemy.
"""

from pathlib import Path

import pytest

from src.models.property import Property, ScrapedListing
from src.models.types import ListingType
from src.storage.repository import PropertyRepository


@pytest.fixture
def repository(tmp_path: Path) -> PropertyRepository:
    return PropertyRepository(db_url=tmp_path / "test.db")


def _listing(listing_id: str, **overrides) -> ScrapedListing:
    payload = {
        "link": f"https://www.otodom.pl/pl/oferta/x-{listing_id}",
        "price": 1_000_000,
        "location": "ul. Test, Warszawa",
    }
    payload.update(overrides)
    return ScrapedListing(**payload)


def test_save_raw_inserts_new_rows(repository):
    written = repository.save_raw(
        [_listing("IDaaa"), _listing("IDbbb")], ListingType.SALE
    )
    assert written == 2

    df = repository.load_raw(ListingType.SALE)
    assert set(df["id"]) == {"IDaaa", "IDbbb"}
    assert all(df["listing_type"] == "sale")


def test_save_raw_upserts_on_conflict(repository):
    repository.save_raw([_listing("IDaaa", price=500)], ListingType.SALE)
    repository.save_raw([_listing("IDaaa", price=999)], ListingType.SALE)

    df = repository.load_raw(ListingType.SALE)
    assert len(df) == 1
    assert df.loc[0, "price"] == 999


def test_save_raw_empty_is_noop(repository):
    assert repository.save_raw([], ListingType.SALE) == 0
    assert repository.load_raw(ListingType.SALE).empty


def test_existing_ids_filters_by_listing_type(repository):
    repository.save_raw([_listing("IDaaa"), _listing("IDbbb")], ListingType.SALE)
    repository.save_raw([_listing("IDccc")], ListingType.RENT)

    assert repository.existing_ids(ListingType.SALE) == {"IDaaa", "IDbbb"}
    assert repository.existing_ids(ListingType.RENT) == {"IDccc"}


def test_save_cleaned_round_trip(repository):
    prop = Property(
        id="IDaaa",
        link="https://www.otodom.pl/pl/oferta/x-IDaaa",
        price=9_600_000,
        area=48.07,
        rooms=3,
        elevator=True,
        district="Śródmieście",
        balcony=True,
    )
    written = repository.save_cleaned([prop], ListingType.SALE)
    assert written == 1

    df = repository.load_cleaned(ListingType.SALE)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["id"] == "IDaaa"
    assert row["price"] == 9_600_000
    assert row["area"] == pytest.approx(48.07)
    assert bool(row["elevator"]) is True
    assert bool(row["balcony"]) is True
    assert row["district"] == "Śródmieście"


def test_save_cleaned_upserts(repository):
    prop_v1 = Property(
        id="IDaaa",
        link="https://www.otodom.pl/pl/oferta/x-IDaaa",
        price=100,
    )
    prop_v2 = prop_v1.model_copy(update={"price": 200})

    repository.save_cleaned([prop_v1], ListingType.SALE)
    repository.save_cleaned([prop_v2], ListingType.SALE)

    df = repository.load_cleaned(ListingType.SALE)
    assert len(df) == 1
    assert df.loc[0, "price"] == 200


def test_load_returns_empty_dataframe_when_no_rows(repository):
    df = repository.load_raw(ListingType.SALE)
    assert df.empty
    cleaned = repository.load_cleaned(ListingType.SALE)
    assert cleaned.empty
