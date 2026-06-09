"""SQLAlchemy ORM tables for raw scraped listings and cleaned properties."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RawListingRow(Base):
    """Snapshot of raw scraped data — append-only with scraped_at timestamp."""

    __tablename__ = "raw_listings"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    link: Mapped[str] = mapped_column(String, nullable=False)
    listing_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    area: Mapped[str | None] = mapped_column(String, nullable=True)
    rooms: Mapped[str | None] = mapped_column(String, nullable=True)
    heating: Mapped[str | None] = mapped_column(String, nullable=True)
    floor: Mapped[str | None] = mapped_column(String, nullable=True)
    maintenance_fee: Mapped[str | None] = mapped_column(String, nullable=True)
    condition: Mapped[str | None] = mapped_column(String, nullable=True)
    market: Mapped[str | None] = mapped_column(String, nullable=True)
    ownership: Mapped[str | None] = mapped_column(String, nullable=True)
    advertiser_type: Mapped[str | None] = mapped_column(String, nullable=True)
    year_built: Mapped[str | None] = mapped_column(String, nullable=True)
    elevator: Mapped[str | None] = mapped_column(String, nullable=True)
    building_type: Mapped[str | None] = mapped_column(String, nullable=True)
    windows: Mapped[str | None] = mapped_column(String, nullable=True)
    security: Mapped[str | None] = mapped_column(String, nullable=True)
    additional_features: Mapped[str | None] = mapped_column(String, nullable=True)


class PropertyRow(Base):
    """Cleaned, typed property — one row per cleaning run."""

    __tablename__ = "properties"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    link: Mapped[str] = mapped_column(String, nullable=False)
    listing_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    cleaned_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area: Mapped[float | None] = mapped_column(Float, nullable=True)
    rooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    maintenance_fee: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_built: Mapped[int | None] = mapped_column(Integer, nullable=True)

    heating: Mapped[str | None] = mapped_column(String, nullable=True)
    condition: Mapped[str | None] = mapped_column(String, nullable=True)
    market: Mapped[str | None] = mapped_column(String, nullable=True)
    ownership: Mapped[str | None] = mapped_column(String, nullable=True)
    advertiser_type: Mapped[str | None] = mapped_column(String, nullable=True)
    building_type: Mapped[str | None] = mapped_column(String, nullable=True)
    windows: Mapped[str | None] = mapped_column(String, nullable=True)

    elevator: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    district: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    neighborhood: Mapped[str | None] = mapped_column(String, nullable=True)
    street: Mapped[str | None] = mapped_column(String, nullable=True)

    current_floor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_floors: Mapped[int | None] = mapped_column(Integer, nullable=True)

    gated_area: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    monitoring: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    security_guard: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    balcony: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    parking: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    terrace: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    garden: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    basement: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    utility_rooms: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    non_smokers_only: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    students_allowed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    separate_kitchen: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
