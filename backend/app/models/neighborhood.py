"""SQLAlchemy ORM model for neighborhood livability and intelligence data."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Neighborhood(Base):
    """
    Stores livability, demographic, and amenity data for a named neighborhood
    within a city. Used to enrich property listings with geo-intelligence.
    """

    __tablename__ = "neighborhoods"

    # ── Primary Key ────────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Location ───────────────────────────────────────────────────────────────
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    neighborhood_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    # e.g., "East Austin", "Brickell", "Capitol Hill"

    zip_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Walkability / Transit Scores (0–100) ──────────────────────────────────
    walk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 0=Car-Dependent, 90-100=Walker's Paradise

    transit_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 0=Minimal Transit, 100=Rider's Paradise

    bike_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 0=Bikeable, 100=Biker's Paradise

    # ── Education ─────────────────────────────────────────────────────────────
    school_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Average school rating 1–10 (e.g., from GreatSchools)

    school_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Number of schools within 1 mile

    # ── Safety ────────────────────────────────────────────────────────────────
    crime_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 0=Safest, 100=Most Dangerous (relative to national average)

    crime_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # "Very Low", "Low", "Medium", "High", "Very High"

    # ── Demographics & Economics ──────────────────────────────────────────────
    median_household_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    # USD per year

    population_density: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # People per square mile

    median_age: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Amenities ─────────────────────────────────────────────────────────────
    restaurant_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grocery_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    park_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gym_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hospital_distance_miles: Mapped[float | None] = mapped_column(Float, nullable=True)

    top_amenities: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON array of strings, e.g. '["Whole Foods","Zilker Park","6th Street"]'

    # ── Composite Score ───────────────────────────────────────────────────────
    livability_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Computed composite 0–100 livability rating

    # ── Trend Data ─────────────────────────────────────────────────────────────
    popularity_trend: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # "rising", "stable", "declining"

    gentrification_risk: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # "low", "medium", "high"

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
        return (
            f"<Neighborhood id={self.id} name={self.neighborhood_name!r} "
            f"city={self.city!r} livability={self.livability_score}>"
        )
