"""SQLite-backed repository for raw scraped listings and cleaned properties.

Single source of truth for pipeline state. CSV is a downstream export, not a
primary store. Upserts by listing id let scraper runs be idempotent.
"""

from pathlib import Path
from typing import Iterable

import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session, sessionmaker

from ..config import settings
from ..models.property import Property, ScrapedListing
from ..models.types import ListingType
from .models import Base, PropertyRow, RawListingRow


class PropertyRepository:
    def __init__(self, db_url: str | Path | None = None):
        url = db_url or settings.database_url
        if isinstance(url, Path):
            url = f"sqlite:///{url}"
        # ensure parent dir exists for default sqlite path
        if url.startswith("sqlite:///"):
            Path(url.removeprefix("sqlite:///")).parent.mkdir(
                parents=True, exist_ok=True
            )
        self._engine = create_engine(str(url), future=True)
        Base.metadata.create_all(self._engine)
        self._Session: sessionmaker[Session] = sessionmaker(
            self._engine, expire_on_commit=False
        )

    def save_raw(
        self, listings: Iterable[ScrapedListing], listing_type: ListingType
    ) -> int:
        rows = [
            {**listing.model_dump(), "listing_type": listing_type.name.lower()}
            for listing in listings
        ]
        if not rows:
            return 0

        with self._Session.begin() as session:
            stmt = sqlite_insert(RawListingRow).values(rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=[RawListingRow.id],
                set_={
                    col.name: stmt.excluded[col.name]
                    for col in RawListingRow.__table__.columns
                    if col.name != "id"
                },
            )
            session.execute(stmt)
        return len(rows)

    def save_cleaned(
        self, properties: Iterable[Property], listing_type: ListingType
    ) -> int:
        rows = [
            {**prop.model_dump(), "listing_type": listing_type.name.lower()}
            for prop in properties
        ]
        if not rows:
            return 0

        with self._Session.begin() as session:
            stmt = sqlite_insert(PropertyRow).values(rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=[PropertyRow.id],
                set_={
                    col.name: stmt.excluded[col.name]
                    for col in PropertyRow.__table__.columns
                    if col.name != "id"
                },
            )
            session.execute(stmt)
        return len(rows)

    def existing_ids(self, listing_type: ListingType) -> set[str]:
        """Return raw-listing ids already in the DB for resume support."""
        with self._Session() as session:
            rows = session.execute(
                select(RawListingRow.id).where(
                    RawListingRow.listing_type == listing_type.name.lower()
                )
            ).all()
        return {row[0] for row in rows}

    def load_raw(self, listing_type: ListingType) -> pd.DataFrame:
        with self._engine.connect() as conn:
            return pd.read_sql(
                select(RawListingRow).where(
                    RawListingRow.listing_type == listing_type.name.lower()
                ),
                conn,
            )

    def load_cleaned(self, listing_type: ListingType) -> pd.DataFrame:
        with self._engine.connect() as conn:
            return pd.read_sql(
                select(PropertyRow).where(
                    PropertyRow.listing_type == listing_type.name.lower()
                ),
                conn,
            )
