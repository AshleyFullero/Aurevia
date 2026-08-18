"""SQLAlchemy ORM model for monthly market price history time-series data."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PriceHistory(Base):
    """
    Stores monthly aggregated price and investment metrics per market
    (city/state/property_type combination). Used for trend charts and
    market forecasting.
    """

    __tablename__ = "price_history"
    __table_args__ = (
        # Prevent duplicate records for the same market + type + period
        UniqueConstraint("city", "state", "property_type", "period", name="uq_price_history_market_period"),
    )

    # ── Primary Key ────────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Market Key ─────────────────────────────────────────────────────────────
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    property_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="all", index=True
    )
    # "all" | "apartment" | "condo" | "townhouse" | "single_family" | "multi_family"

    # ── Time Period ────────────────────────────────────────────────────────────
    period: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    # ISO YYYY-MM string, e.g. "2024-01", "2024-06"

    # ── Price Metrics ─────────────────────────────────────────────────────────
    avg_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_per_sqft: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Volume & Activity ─────────────────────────────────────────────────────
    transaction_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Number of transactions/listings in this period

    days_on_market_avg: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Investment Metrics ────────────────────────────────────────────────────
    avg_cap_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_rental_yield: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_vacancy_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Growth ─────────────────────────────────────────────────────────────────
    mom_price_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Month-over-month price change as decimal (e.g., 0.02 = 2%)

    yoy_price_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Year-over-year price change as decimal

    # ── Timestamps ─────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<PriceHistory id={self.id} market={self.city},{self.state} "
            f"type={self.property_type!r} period={self.period!r} "
            f"avg_price={self.avg_price}>"
        )
