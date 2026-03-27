from enum import Enum
from typing import Literal

SortDirection = Literal["DESC", "ASC"]


class District(Enum):
    SRODMIESCIE = "mazowieckie/warszawa/warszawa/warszawa/srodmiescie"
    MOKOTOW = "mazowieckie/warszawa/warszawa/warszawa/mokotow"
    OCHOTA = "mazowieckie/warszawa/warszawa/warszawa/ochota"
    WOLA = "mazowieckie/warszawa/warszawa/warszawa/wola"
    ZOLIBORZ = "mazowieckie/warszawa/warszawa/warszawa/zoliborz"
    PRAGA_POLUDNIE = "mazowieckie/warszawa/warszawa/warszawa/praga--poludnie"
    PRAGA_POLNOC = "mazowieckie/warszawa/warszawa/warszawa/praga--polnoc"
    BEMOWO = "mazowieckie/warszawa/warszawa/warszawa/bemowo"
    BIALOLEKA = "mazowieckie/warszawa/warszawa/warszawa/bialoleka"
    BIELANY = "mazowieckie/warszawa/warszawa/warszawa/bielany"
    REMBERTOW = "mazowieckie/warszawa/warszawa/warszawa/rembertow"
    TARGOWEK = "mazowieckie/warszawa/warszawa/warszawa/targowek"
    URSUS = "mazowieckie/warszawa/warszawa/warszawa/ursus"
    URSYNOW = "mazowieckie/warszawa/warszawa/warszawa/ursynow"
    WAWER = "mazowieckie/warszawa/warszawa/warszawa/wawer"
    WESOLA = "mazowieckie/warszawa/warszawa/warszawa/wesola"
    WILANOW = "mazowieckie/warszawa/warszawa/warszawa/wilanow"
    WLOCHY = "mazowieckie/warszawa/warszawa/warszawa/wlochy"


class ResultLimit(Enum):
    SMALL = 24
    MEDIUM = 36
    LARGE = 48
    XLARGE = 72


class PropertyType(Enum):
    APARTMENT = "mieszkanie"
    HOUSE = "dom"


class ListingType(Enum):
    SALE = "sprzedaz"
    RENT = "wynajem"
