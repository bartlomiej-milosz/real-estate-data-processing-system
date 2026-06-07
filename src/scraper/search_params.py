import urllib.parse
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..models.types import (
    District,
    ListingType,
    PropertyType,
    ResultLimit,
    SortDirection,
)

BASE_URL = "https://www.otodom.pl/pl/wyniki"
DEFAULT_PARAMS = {"ownerTypeSingleSelect": "ALL", "by": "DEFAULT", "direction": "DESC"}


@dataclass
class PropertySearchQuery:
    """Configuration class for building Otodom scraper URLs"""

    locations: List[District]
    property_type: PropertyType = PropertyType.APARTMENT
    listing_type: ListingType = ListingType.SALE
    limit: ResultLimit = ResultLimit.MEDIUM
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    direction: Optional[SortDirection] = None

    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.locations:
            raise ValueError("At least one location must be specified")

        if self.price_min is not None and self.price_min < 0:
            raise ValueError("Minimum price cannot be negative")

        if self.price_max is not None and self.price_max < 0:
            raise ValueError("Maximum price cannot be negative")

        if (
            self.price_min is not None
            and self.price_max is not None
            and self.price_min > self.price_max
        ):
            raise ValueError("Minimum price cannot be greater than maximum price")

    def _build_base_url(self) -> str:
        """Build the base URL based on number of locations"""
        prefix = f"{BASE_URL}/{self.listing_type.value}/{self.property_type.value}"
        if len(self.locations) == 1:
            return f"{prefix}/{self.locations[0].value}"
        return f"{prefix}/wiele-lokalizacji"

    def _build_location_params(self) -> Dict[str, str]:
        """Build location-specific parameters"""
        if len(self.locations) > 1:
            locations_list = [district.value for district in self.locations]
            return {"locations": "[" + ",".join(locations_list) + "]"}
        return {}

    def _build_price_params(self) -> Dict[str, str]:
        """Build price-related parameters"""
        params = {}
        if self.price_min is not None:
            params["priceMin"] = str(self.price_min)
        if self.price_max is not None:
            params["priceMax"] = str(self.price_max)
        return params

    def _build_pagination_params(self, page: int) -> Dict[str, str]:
        """Build pagination parameters"""
        return {"page": str(page)} if page > 1 else {}

    def _build_all_params(self, page: int = 1) -> Dict[str, str]:
        """Build all URL parameters"""
        params = {}

        params.update(DEFAULT_PARAMS)
        params["limit"] = str(self.limit.value)
        params.update(self._build_location_params())
        params.update(self._build_price_params())
        params.update(self._build_pagination_params(page))

        if self.direction is not None:
            params["direction"] = self.direction

        return params

    def get_url(self, page: int = 1) -> str:
        """Generate the complete URL for scraping"""
        if page < 1:
            raise ValueError("Page number must be 1 or greater")

        base_url = self._build_base_url()
        params = self._build_all_params(page)
        query_string = urllib.parse.urlencode(params, safe="/")

        return f"{base_url}?{query_string}"

    def get_urls(self, max_pages: int = 1) -> List[str]:
        """Generate multiple URLs for pagination"""
        if max_pages < 1:
            raise ValueError("max_pages must be 1 or greater")

        return [self.get_url(page) for page in range(1, max_pages + 1)]

    def __str__(self) -> str:
        """String representation of the config"""
        return (
            f"ScraperConfig("
            f"locations={len(self.locations)} districts, "
            f"type={self.property_type.value}, "
            f"listing={self.listing_type.value}, "
            f"limit={self.limit.value})"
        )

    def __repr__(self) -> str:
        """Detailed representation for debugging"""
        return (
            f"ScraperConfig("
            f"locations={[d.name for d in self.locations]}, "
            f"property_type='{self.property_type.value}', "
            f"listing_type='{self.listing_type.value}', "
            f"limit={self.limit}, "
            f"price_min={self.price_min}, "
            f"price_max={self.price_max}, "
            f"direction={self.direction})"
        )
