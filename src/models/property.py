"""Domain models.

Two layers:
* `ScrapedListing` — raw strings exactly as pulled from otodom. Used by the
  scraper. No domain semantics; survives schema changes on the source side.
* `Property` — cleaned, typed representation produced by the cleaner.
"""

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

_ID_PATTERN = re.compile(r"-(?P<id>ID[A-Za-z0-9]+)/?$")


def extract_listing_id(url: str) -> Optional[str]:
    """Pull the otodom listing id (e.g. 'ID4qABc') from a detail page URL."""
    match = _ID_PATTERN.search(url.rstrip("/"))
    return match.group("id") if match else None


class ScrapedListing(BaseModel):
    """Raw scraped data — string-based, lenient."""

    model_config = ConfigDict(frozen=True)

    link: str
    id: str = Field(default="")

    price: Optional[int] = None
    location: Optional[str] = None

    area: Optional[str] = None
    rooms: Optional[str] = None
    heating: Optional[str] = None
    floor: Optional[str] = None
    maintenance_fee: Optional[str] = None
    condition: Optional[str] = None
    market: Optional[str] = None
    ownership: Optional[str] = None
    advertiser_type: Optional[str] = None

    year_built: Optional[str] = None
    elevator: Optional[str] = None
    building_type: Optional[str] = None
    windows: Optional[str] = None
    security: Optional[str] = None

    additional_features: Optional[str] = None

    @model_validator(mode="after")
    def _derive_id(self) -> "ScrapedListing":
        if not self.id:
            listing_id = extract_listing_id(self.link)
            if listing_id is None:
                raise ValueError(
                    f"Cannot extract otodom listing id from URL: {self.link}"
                )
            object.__setattr__(self, "id", listing_id)
        return self


class Property(BaseModel):
    """Cleaned property with typed fields. Output of the cleaning pipeline."""

    model_config = ConfigDict(frozen=True)

    id: str
    link: str

    price: Optional[int] = None
    area: Optional[float] = None
    rooms: Optional[int] = None
    maintenance_fee: Optional[int] = None
    year_built: Optional[int] = None

    heating: Optional[str] = None
    condition: Optional[str] = None
    market: Optional[str] = None
    ownership: Optional[str] = None
    advertiser_type: Optional[str] = None
    building_type: Optional[str] = None
    windows: Optional[str] = None

    elevator: Optional[bool] = None

    district: Optional[str] = None
    neighborhood: Optional[str] = None
    street: Optional[str] = None

    current_floor: Optional[int] = None
    total_floors: Optional[int] = None

    gated_area: Optional[bool] = None
    monitoring: Optional[bool] = None
    security_guard: Optional[bool] = None

    balcony: Optional[bool] = None
    parking: Optional[bool] = None
    terrace: Optional[bool] = None
    garden: Optional[bool] = None
    basement: Optional[bool] = None
    utility_rooms: Optional[bool] = None
    non_smokers_only: Optional[bool] = None
    students_allowed: Optional[bool] = None
    separate_kitchen: Optional[bool] = None
