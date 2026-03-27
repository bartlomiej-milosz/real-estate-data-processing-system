import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Property:
    link: str
    id: str = field(default_factory=lambda: Property._generate_smart_id())

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

    @staticmethod
    def _generate_smart_id() -> str:
        now = datetime.now()
        # date_part = now.strftime("%Y%m%d")
        time_part = now.strftime("%H%M%S")
        random_part = random.randint(100, 999)
        return f"{random_part}{time_part}"
