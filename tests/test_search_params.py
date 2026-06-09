"""Tests for the otodom search URL builder."""

from urllib.parse import parse_qs, unquote, urlparse

import pytest

from src.models.types import District, ListingType, PropertyType, ResultLimit
from src.scraper.search_params import PropertySearchQuery


def _query(url: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(url).query)


def test_single_district_uses_path_form():
    q = PropertySearchQuery(
        locations=[District.SRODMIESCIE],
        listing_type=ListingType.SALE,
        property_type=PropertyType.APARTMENT,
        limit=ResultLimit.LARGE,
    )
    url = q.get_url()
    expected = "/sprzedaz/mieszkanie/mazowieckie/warszawa/warszawa/warszawa/srodmiescie"
    assert expected in url
    assert "locations" not in _query(url)


def test_multiple_districts_use_wiele_lokalizacji():
    q = PropertySearchQuery(
        locations=[District.SRODMIESCIE, District.MOKOTOW],
        listing_type=ListingType.RENT,
    )
    url = q.get_url()
    parsed = urlparse(url)
    assert parsed.path.endswith("/wynajem/mieszkanie/wiele-lokalizacji")

    locations = unquote(_query(url)["locations"][0])
    assert locations == (
        "[mazowieckie/warszawa/warszawa/warszawa/srodmiescie,"
        "mazowieckie/warszawa/warszawa/warszawa/mokotow]"
    )


def test_price_filters_emitted_only_when_set():
    base = PropertySearchQuery(locations=[District.WOLA])
    assert "priceMin" not in _query(base.get_url())
    assert "priceMax" not in _query(base.get_url())

    bounded = PropertySearchQuery(
        locations=[District.WOLA], price_min=1000, price_max=5000
    )
    qs = _query(bounded.get_url())
    assert qs["priceMin"] == ["1000"]
    assert qs["priceMax"] == ["5000"]


def test_page_param_omitted_for_first_page():
    q = PropertySearchQuery(locations=[District.WOLA])
    assert "page" not in _query(q.get_url(page=1))
    assert _query(q.get_url(page=3))["page"] == ["3"]


def test_limit_value_encoded():
    q = PropertySearchQuery(locations=[District.WOLA], limit=ResultLimit.XLARGE)
    assert _query(q.get_url())["limit"] == ["72"]


def test_empty_locations_raises():
    with pytest.raises(ValueError, match="(?i)at least one location"):
        PropertySearchQuery(locations=[])


def test_invalid_price_range_raises():
    with pytest.raises(ValueError, match="greater than maximum"):
        PropertySearchQuery(locations=[District.WOLA], price_min=5000, price_max=1000)


def test_negative_price_raises():
    with pytest.raises(ValueError, match="negative"):
        PropertySearchQuery(locations=[District.WOLA], price_min=-1)


def test_page_below_one_raises():
    q = PropertySearchQuery(locations=[District.WOLA])
    with pytest.raises(ValueError):
        q.get_url(page=0)


def test_get_urls_paginates():
    q = PropertySearchQuery(locations=[District.WOLA])
    urls = q.get_urls(max_pages=3)
    assert len(urls) == 3
    assert "page" not in _query(urls[0])
    assert _query(urls[1])["page"] == ["2"]
    assert _query(urls[2])["page"] == ["3"]
