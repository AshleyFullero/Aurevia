"""SQLAlchemy ORM model for session-based investment portfolio tracking."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PortfolioEntry(Base):
    """
    A single property position in an investor's tracked portfolio.
    Session-based (no auth required for MVP) — swap session_token
    for a real user FK when authentication is added.
    """

    __tablename__ = "portfolio_entries"
    __table_args__ = (
        # Prevent the same user from adding the same property twice
        UniqueConstraint("session_token", "property_id", name="uq_portfolio_session_property"),
    )

    # ── Primary Key ────────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Session / User ─────────────────────────────────────────────────────────
    session_token: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    # UUID from localStorage — swapped for user_id once auth lands

    # ── Property Reference ─────────────────────────────────────────────────────
    property_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Purchase / Acquisition Details ────────────────────────────────────────
    purchase_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Actual purchase price (may differ from list_price)

    purchase_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)

    down_payment_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Decimal, e.g., 0.20 for 20% down

    mortgage_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Annual interest rate as decimal, e.g., 0.065 = 6.5%

    loan_term_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # e.g., 30 for a 30-year mortgage

    # ── Rental Income (actual / override) ────────────────────────────────────
    actual_monthly_rent: Mapped[float | None] = mapped_column(Float, nullable=True)
    # If None, uses property.monthly_rent_estimate from the property table

    # ── Notes ──────────────────────────────────────────────────────────────────
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Free-form investor notes about this position

    # ── Status ─────────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )
    # "active" | "sold" | "under_contract" | "watchlist"

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
            f"<PortfolioEntry id={self.id} property_id={self.property_id} "
            f"session={self.session_token[:8]}... status={self.status!r}>"
        )
