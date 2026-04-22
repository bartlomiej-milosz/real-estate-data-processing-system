"""Pure HTML -> dict parsing for otodom listing and detail pages.

These functions are deliberately free of HTTP or threading concerns so they can
be unit-tested against saved HTML fixtures without network access.
"""

import logging
import urllib.parse
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup, Tag

from .config import ALL_DETAILS

logger = logging.getLogger(__name__)

BASE_URL = "https://www.otodom.pl"


def parse_listing_links(html: str) -> List[str]:
    """Extract detail page URLs from a search results page."""
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("a", {"data-cy": "listing-item-link"})
    links: List[str] = []
    for card in cards:
        href = card.get("href")
        if href:
            links.append(urllib.parse.urljoin(BASE_URL, href))
    return links


def parse_property_detail(html: str) -> Dict[str, Any]:
    """Parse a property detail page into a flat dict of raw strings/ints."""
    soup = BeautifulSoup(html, "html.parser")
    data: Dict[str, Any] = {
        "price": _extract_price(soup),
        "location": _extract_location(soup),
    }
    for field_name, polish_label in ALL_DETAILS.items():
        data[field_name] = _extract_field_by_label(soup, polish_label)
    data["additional_features"] = _extract_additional_features(soup)
    return data


def _extract_price(soup: BeautifulSoup) -> Optional[int]:
    try:
        price_tag = soup.find(
            "strong",
            {
                "data-cy": "adPageHeaderPrice",
                "data-sentry-element": "Price",
                "data-sentry-source-file": "AdPrice.tsx",
            },
        )
        if not price_tag:
            return None
        digits = "".join(filter(str.isdigit, price_tag.text.strip()))
        return int(digits) if digits else None
    except (AttributeError, ValueError) as e:
        logger.warning(f"Could not extract price: {e}")
        return None


def _extract_location(soup: BeautifulSoup) -> Optional[str]:
    try:
        tag = soup.find(
            "a",
            {
                "data-sentry-element": "StyledLink",
                "data-sentry-source-file": "MapLink.tsx",
            },
        )
        return tag.text if tag else None
    except AttributeError as e:
        logger.warning(f"Could not extract location: {e}")
        return None


def _find_item_containers(soup: BeautifulSoup) -> List[Tag]:
    return soup.find_all(
        "div",
        {
            "data-sentry-element": "ItemGridContainer",
            "data-sentry-source-file": "AdDetailItem.tsx",
        },
    )


def _find_label_container(container: Tag, label_text: str) -> Optional[Tag]:
    label_div = container.find(
        "div",
        {
            "data-sentry-element": "Item",
            "data-sentry-source-file": "AdDetailItem.tsx",
        },
    )
    if label_div and label_text in label_div.get_text():
        return label_div
    return None


def _extract_field_by_label(soup: BeautifulSoup, label_text: str) -> Optional[str]:
    try:
        for container in _find_item_containers(soup):
            label_div = _find_label_container(container, label_text)
            if label_div:
                value_div = label_div.find_next_sibling("div")
                if value_div:
                    return value_div.get_text(strip=True)
        return None
    except AttributeError as e:
        logger.warning(f"Could not extract field '{label_text}': {e}")
        return None


def _extract_additional_features(soup: BeautifulSoup) -> Optional[str]:
    try:
        for container in _find_item_containers(soup):
            label_div = _find_label_container(container, "Informacje dodatkowe:")
            if not label_div:
                continue
            features_div = label_div.find_next_sibling("div")
            if not features_div:
                continue
            spans = features_div.find_all("span", class_="css-axw7ok")
            features = [s.get_text(strip=True) for s in spans if s.get_text(strip=True)]
            if features:
                return " | ".join(features)
        return None
    except AttributeError as e:
        logger.warning(f"Could not extract additional features: {e}")
        return None
