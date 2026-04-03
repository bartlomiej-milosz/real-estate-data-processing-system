import re
from dataclasses import dataclass, field
from typing import Optional

_ID_PATTERN = re.compile(r"-(?P<id>ID[A-Za-z0-9]+)/?$")


def extract_listing_id(url: str) -> Optional[str]:
    """Pull the otodom listing id (e.g. 'ID4qABc') from a detail page URL."""
    match = _ID_PATTERN.search(url.rstrip("/"))
    return match.group("id") if match else None


@dataclass
class Property:
    link: str
    id: str = field(init=False)

    # Basic info
    price: Optional[int] = None
    location: Optional[str] = None

    # Property details (raw text)
    area: Optional[str] = None
    rooms: Optional[str] = None
    heating: Optional[str] = None
    floor: Optional[str] = None
    maintenance_fee: Optional[str] = None
    condition: Optional[str] = None
    market: Optional[str] = None
    ownership: Optional[str] = None
    advertiser_type: Optional[str] = None

    # Building details (raw text)
    year_built: Optional[str] = None
    elevator: Optional[str] = None
    building_type: Optional[str] = None
    windows: Optional[str] = None
    security: Optional[str] = None

    # Additional features
    additional_features: Optional[str] = None

    def __post_init__(self) -> None:
        listing_id = extract_listing_id(self.link)
        if listing_id is None:
            raise ValueError(f"Cannot extract otodom listing id from URL: {self.link}")
        self.id = listing_id
