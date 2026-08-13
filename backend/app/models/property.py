"""SQLAlchemy ORM model for real estate properties."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Property(Base):
    """Represents a real estate listing in the database."""

    __tablename__ = "properties"

    # ── Primary Key ────────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Location ───────────────────────────────────────────────────────────────
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    zip_code: Mapped[str] = mapped_column(String(20), nullable=False)
    neighborhood: Mapped[str | None] = mapped_column(String(150), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Property Details ──────────────────────────────────────────────────────
    bedrooms: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    bathrooms: Mapped[float] = mapped_column(Float, nullable=False)
    square_feet: Mapped[int] = mapped_column(Integer, nullable=False)
    property_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # e.g. "apartment", "condo", "townhouse", "single_family", "multi_family"

    year_built: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Pricing ────────────────────────────────────────────────────────────────
    list_price: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    price_per_sqft: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Aurevia's estimated fair value (AI-calculated)
    fair_value_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Investment Metrics ────────────────────────────────────────────────────
    cap_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Capitalization rate as a decimal (e.g., 0.084 = 8.4%)

    rental_yield: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Gross rental yield as a decimal

    monthly_rent_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)

    five_year_appreciation: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Projected 5-year appreciation as a decimal

    yoy_growth: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Year-over-year price growth as a decimal

    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 0-100, lower is safer

    vacancy_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Local vacancy rate as a decimal

    # ── Status ─────────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    days_on_market: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Timestamps ─────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Property id={self.id} address={self.address!r} price={self.list_price}>"
