import logging
import urllib
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup, Tag

from ..models.property import Property
from .config import ALL_DETAILS, HEADERS
from .search_params import PropertySearchQuery

logger = logging.getLogger(__name__)

BASE_URL: str = "https://www.otodom.pl"


class PropertyScraper:
    def __init__(self, config: PropertySearchQuery):
        self.config: PropertySearchQuery = config
        self.properties: List[Property] = []
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def get_properties(self) -> List[Property]:
        """Get list of scraped properties"""
        return self.properties

    def get_properties_count(self) -> int:
        """Get number of scraped properties"""
        return len(self.properties)

    def _extract_links(self, card_elements) -> List[str]:
        """Helper function for extracting href from given <a> element"""
        card_links: List[str] = []
        for listing_card in card_elements:
            href = listing_card.get("href")
            if href:
                full_url = urllib.parse.urljoin(BASE_URL, href)
                card_links.append(full_url)
        logger.info(f"Extracted {len(card_links)} valid links")
        return card_links

    def _get_listing_card_links(self, page: int = 1) -> List[str]:
        """Retrieves all property listing URLs from the specified page"""

        if page < 1:
            raise ValueError("Page must be 1 or greater")

        try:
            logger.info(f"Fetching page {page}")
            url: str = self.config.get_url(page=page)
            response = self.session.get(url)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.content, "html.parser")
            listing_card_elements = soup.find_all("a", {"data-cy": "listing-item-link"})
            logger.info(f"Found {len(listing_card_elements)} listings")
            return self._extract_links(listing_card_elements)
        except requests.RequestException as e:
            logger.error(f"Error fetching page {page}: {e}")
            return []

    def _get_price(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract price from listing detail page"""
        try:
            price_tag = soup.find(
                "strong",
                {
                    "data-cy": "adPageHeaderPrice",
                    "data-sentry-element": "Price",
                    "data-sentry-source-file": "AdPrice.tsx",
                },
            )

            if price_tag:
                price_text = price_tag.text.strip()
                price_numbers = "".join(filter(str.isdigit, price_text))
                return int(price_numbers) if price_numbers else None

            return None
        except Exception as e:
            logger.warning(f"Could not extract price: {e}")
            return None

    def _get_location(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract location from listing detail page"""
        try:
            location_tag = soup.find(
                "a",
                {
                    "data-sentry-element": "StyledLink",
                    "data-sentry-source-file": "MapLink.tsx",
                },
            )
            if location_tag:
                return location_tag.text
            return None
        except Exception as e:
            logger.warning(f"Could not extract location: {e}")
            return None

    def _find_item_containers(self, soup: BeautifulSoup) -> List:
        """Find all ItemGridContainer elements"""
        return soup.find_all(
            "div",
            {
                "data-sentry-element": "ItemGridContainer",
                "data-sentry-source-file": "AdDetailItem.tsx",
            },
        )

    def _find_label_container(self, container, label_text: str) -> Optional[Any]:
        """Find container with matching label text"""
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

    def _find_field_value_by_label(
        self, soup: BeautifulSoup, label_text: str
    ) -> Optional[str]:
        """Universal function to find field value by label in ItemGridContainer"""
        try:
            containers: List[Tag] = self._find_item_containers(soup)
            for container in containers:
                label_div: Optional[Tag] = self._find_label_container(
                    container, label_text
                )
                if label_div:
                    value_div: Optional[Tag] = label_div.find_next_sibling("div")
                    if value_div:
                        return value_div.get_text(strip=True)
            return None
        except Exception as e:
            logger.warning(f"Could not extract field '{label_text}': {e}")
            return None

    def _get_additional_features(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract additional features as pipe-separated string"""
        try:
            containers = self._find_item_containers(soup)

            for container in containers:
                label_div = self._find_label_container(
                    container, "Informacje dodatkowe:"
                )

                if label_div:
                    features_div = label_div.find_next_sibling("div")
                    if features_div:
                        spans = features_div.find_all("span", class_="css-axw7ok")
                        features = [
                            span.get_text(strip=True)
                            for span in spans
                            if span.get_text(strip=True)
                        ]

                        if features:
                            return " | ".join(features)

            return None
        except Exception as e:
            logger.warning(f"Could not extract additional features: {e}")
            return None

    def _extract_all_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        property_data: Dict[str, Any] = {}

        # Extract price and location with custom methods
        property_data["price"] = self._get_price(soup)
        property_data["location"] = self._get_location(soup)

        # Extract all mapped fields
        for field_name, polish_label in ALL_DETAILS.items():
            property_data[field_name] = self._find_field_value_by_label(
                soup, polish_label
            )

        # Extract additional features
        property_data["additional_features"] = self._get_additional_features(soup)

        return property_data

    def _scrape_single_property(self, detail_link: str) -> Optional[Property]:
        try:
            logger.info(f"Scraping: {detail_link}")

            response = self.session.get(detail_link)
            response.raise_for_status()
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.content, "html.parser")

            property_data: Dict[str, Any] = self._extract_all_details(soup)

            property_obj = Property(
                link=detail_link,
                price=property_data.get("price"),
                location=property_data.get("location"),
                area=property_data.get("area"),
                rooms=property_data.get("rooms"),
                heating=property_data.get("heating"),
                floor=property_data.get("floor"),
                maintenance_fee=property_data.get("maintenance_fee"),
                condition=property_data.get("condition"),
                market=property_data.get("market"),
                ownership=property_data.get("ownership"),
                advertiser_type=property_data.get("advertiser_type"),
                year_built=property_data.get("year_built"),
                elevator=property_data.get("elevator"),
                building_type=property_data.get("building_type"),
                windows=property_data.get("windows"),
                security=property_data.get("security"),
                additional_features=property_data.get("additional_features"),
            )

            logger.info(f"Scraped: {property_obj}")
            return property_obj

        except Exception as e:
            logger.error(f"Failed to scrape {detail_link}: {e}")
            return None

    def scrape_single_page_details(self, page: int = 1) -> List[Property]:
        """Scrape one page and return properties - THREADED VERSION"""

        listing_card_links: List[str] = self._get_listing_card_links(page=page)

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(
                executor.map(self._scrape_single_property, listing_card_links)
            )

        page_properties = [prop for prop in results if prop is not None]

        return page_properties

    def scrape_multiple_pages(self, max_pages: int) -> None:
        """Scrape multiple pages"""
        logger.info(f"Starting scrape for {max_pages} pages")

        for page in range(1, max_pages + 1):
            logger.info(f"Processing page {page}/{max_pages}")

            page_properties: List[Property] = self.scrape_single_page_details(page)
            self.properties.extend(page_properties)

            logger.info(f"Page {page} done: {len(page_properties)} properties")

        logger.info(f"Finished! Total: {len(self.properties)} properties")
