"""SQLAlchemy ORM model for investor reviews and platform testimonials."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Review(Base):
    """Represents a user/investor testimonial or platform review."""

    __tablename__ = "reviews"

    # ── Primary Key ────────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Reviewer Identity ──────────────────────────────────────────────────────
    reviewer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    reviewer_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # e.g., "Senior Portfolio Manager", "Real Estate Investor"

    reviewer_company: Mapped[str | None] = mapped_column(String(150), nullable=True)
    # e.g., "BlackRock Real Estate", "Apex Capital"

    avatar_initials: Mapped[str] = mapped_column(String(4), nullable=False, default="??")
    # Up to 2 characters shown as avatar placeholder (e.g., "JK")

    avatar_color: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # CSS color class or hex for avatar background (e.g., "#4F46E5")

    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # City, State — e.g., "Austin, TX"

    # ── Review Content ─────────────────────────────────────────────────────────
    rating: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # 1–5 star rating

    headline: Mapped[str] = mapped_column(String(250), nullable=False)
    # Short punchy headline, e.g., "Found a 9.2% cap rate deal in 2 days"

    body: Mapped[str] = mapped_column(Text, nullable=False)
    # Full review text

    # ── Metrics Mentioned ─────────────────────────────────────────────────────
    # Optional structured metrics the reviewer mentions, for highlight display
    highlight_metric: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # e.g., "9.2% cap rate", "$14K/month", "62% time saved"

    highlight_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # e.g., "Deal Found", "Monthly Income", "Time Saved"

    # ── Platform Metadata ──────────────────────────────────────────────────────
    is_featured: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    # Featured reviews appear prominently in the social-proof section

    source: Mapped[str] = mapped_column(String(50), nullable=False, default="platform")
    # "platform" | "google" | "trustpilot" | "linkedin" | "imported"

    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Verified purchase/platform user

    helpful_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # How many users found this helpful

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
            f"<Review id={self.id} reviewer={self.reviewer_name!r} "
            f"rating={self.rating} featured={self.is_featured}>"
        )
