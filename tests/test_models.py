"""Tests for pydantic models and the listing-id helper."""

import pytest
from pydantic import ValidationError

from src.models.property import Property, ScrapedListing, extract_listing_id


def test_extract_listing_id_pulls_otodom_suffix():
    assert (
        extract_listing_id("https://www.otodom.pl/pl/oferta/foo-bar-ID4qABc")
        == "ID4qABc"
    )
    assert (
        extract_listing_id("https://www.otodom.pl/pl/oferta/foo-bar-ID4qABc/")
        == "ID4qABc"
    )


def test_extract_listing_id_returns_none_when_missing():
    assert extract_listing_id("https://example.com/no-id-here") is None


def test_scraped_listing_derives_id_from_link():
    listing = ScrapedListing(link="https://www.otodom.pl/pl/oferta/x-IDabc")
    assert listing.id == "IDabc"


def test_scraped_listing_rejects_link_without_id():
    with pytest.raises(ValidationError, match="Cannot extract"):
        ScrapedListing(link="https://example.com/no-id")


def test_scraped_listing_is_frozen():
    listing = ScrapedListing(link="https://www.otodom.pl/pl/oferta/x-IDabc")
    with pytest.raises(ValidationError):
        listing.price = 100


def test_scraped_listing_coerces_numeric_strings():
    listing = ScrapedListing(
        link="https://www.otodom.pl/pl/oferta/x-IDabc",
        year_built=1939,  # int gets coerced to str
        area=48.07,
    )
    assert listing.year_built == "1939"
    assert listing.area == "48.07"


def test_property_validates_types():
    prop = Property(
        id="IDabc",
        link="https://www.otodom.pl/pl/oferta/x-IDabc",
        price=9_600_000,
        area=48.07,
        rooms=3,
        elevator=True,
    )
    assert prop.price == 9_600_000
    assert prop.area == 48.07
    assert prop.rooms == 3
    assert prop.elevator is True


def test_property_is_frozen():
    prop = Property(id="IDabc", link="https://www.otodom.pl/pl/oferta/x-IDabc")
    with pytest.raises(ValidationError):
        prop.price = 100
