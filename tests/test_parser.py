"""Unit tests for the otodom HTML parser.

Uses minimal synthetic HTML that exercises the exact selectors the production
parser relies on. Decoupled from network so tests stay fast and deterministic.
"""

from textwrap import dedent

from src.scraper.parser import (
    parse_listing_links,
    parse_property_detail,
)


def _detail_field(label: str, value: str) -> str:
    return dedent(f"""\
        <div data-sentry-element="ItemGridContainer"
             data-sentry-source-file="AdDetailItem.tsx">
          <div data-sentry-element="Item"
               data-sentry-source-file="AdDetailItem.tsx">{label}</div>
          <div>{value}</div>
        </div>
    """)


def test_parse_listing_links_returns_absolute_urls():
    html = """
        <html><body>
          <a data-cy="listing-item-link" href="/pl/oferta/foo-IDabc"></a>
          <a data-cy="listing-item-link" href="https://www.otodom.pl/pl/oferta/bar-IDxyz"></a>
          <a data-cy="listing-item-link"></a>
          <a href="/pl/oferta/not-a-listing"></a>
        </body></html>
    """
    links = parse_listing_links(html)
    assert links == [
        "https://www.otodom.pl/pl/oferta/foo-IDabc",
        "https://www.otodom.pl/pl/oferta/bar-IDxyz",
    ]


def test_parse_listing_links_empty():
    assert parse_listing_links("<html><body></body></html>") == []


def test_parse_property_detail_price_and_location():
    html = """
        <html><body>
          <strong data-cy="adPageHeaderPrice"
                  data-sentry-element="Price"
                  data-sentry-source-file="AdPrice.tsx">9 600 000 zł</strong>
          <a data-sentry-element="StyledLink"
             data-sentry-source-file="MapLink.tsx">ul. Grzybowska, Śródmieście, Warszawa</a>
        </body></html>
    """
    data = parse_property_detail(html)
    assert data["price"] == 9_600_000
    assert data["location"] == "ul. Grzybowska, Śródmieście, Warszawa"


def test_parse_property_detail_missing_returns_none():
    data = parse_property_detail("<html><body></body></html>")
    assert data["price"] is None
    assert data["location"] is None
    assert data["area"] is None
    assert data["additional_features"] is None


def test_parse_property_detail_fields_by_label():
    fields = [
        ("Powierzchnia:", "48,07 m²"),
        ("Liczba pokoi:", "3"),
        ("Piętro:", "5/10"),
        ("Czynsz:", "850 zł"),
        ("Rok budowy:", "1939"),
        ("Winda:", "tak"),
        ("Bezpieczeństwo:", "teren zamknięty, monitoring"),
    ]
    inner = "\n".join(_detail_field(label, value) for label, value in fields)
    html = f"<html><body>{inner}</body></html>"

    data = parse_property_detail(html)
    assert data["area"] == "48,07 m²"
    assert data["rooms"] == "3"
    assert data["floor"] == "5/10"
    assert data["maintenance_fee"] == "850 zł"
    assert data["year_built"] == "1939"
    assert data["elevator"] == "tak"
    assert data["security"] == "teren zamknięty, monitoring"


def test_parse_property_detail_additional_features_pipe_joined():
    html = f"""
        <html><body>
          {_detail_field(
              "Informacje dodatkowe:",
              '<span class="css-axw7ok">balkon</span>'
              '<span class="css-axw7ok">piwnica</span>'
              '<span class="css-axw7ok"></span>'
              '<span class="css-axw7ok">taras</span>',
          )}
        </body></html>
    """
    data = parse_property_detail(html)
    assert data["additional_features"] == "balkon | piwnica | taras"


def test_parse_property_detail_dirty_price_extracts_digits_only():
    html = """
        <html><body>
          <strong data-cy="adPageHeaderPrice"
                  data-sentry-element="Price"
                  data-sentry-source-file="AdPrice.tsx">12 500.00 zł</strong>
        </body></html>
    """
    assert parse_property_detail(html)["price"] == 1_250_000
