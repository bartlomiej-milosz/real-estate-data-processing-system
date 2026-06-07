from typing import Dict

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
_ACCEPT = (
    "text/html,application/xhtml+xml,application/xml;q=0.9,"
    "image/avif,image/webp,*/*;q=0.8"
)

HEADERS: Dict[str, str] = {
    "User-Agent": _USER_AGENT,
    "Accept": _ACCEPT,
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Referer": "https://www.otodom.pl",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Upgrade-Insecure-Requests": "1",
}

PROPERTY_DETAILS = {
    "area": "Powierzchnia:",
    "rooms": "Liczba pokoi:",
    "heating": "Ogrzewanie:",
    "floor": "Piętro:",
    "maintenance_fee": "Czynsz:",
    "condition": "Stan wykończenia:",
    "market": "Rynek:",
    "ownership": "Forma własności:",
    "advertiser_type": "Typ ogłoszeniodawcy:",
}

BUILDING_DETAILS = {
    "year_built": "Rok budowy:",
    "elevator": "Winda:",
    "building_type": "Rodzaj zabudowy:",
    "windows": "Okna:",
    "security": "Bezpieczeństwo:",
}

ALL_DETAILS = {**PROPERTY_DETAILS, **BUILDING_DETAILS}
