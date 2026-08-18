"""Pydantic schemas for Review request/response validation."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ── Review Create ──────────────────────────────────────────────────────────────
class ReviewCreate(BaseModel):
    """Request body to submit a new platform review."""

    reviewer_name: str = Field(..., min_length=2, max_length=150, description="Full name of the reviewer")
    reviewer_title: Optional[str] = Field(None, max_length=200)
    reviewer_company: Optional[str] = Field(None, max_length=150)
    avatar_initials: str = Field(..., min_length=1, max_length=4, description="1–2 char initials shown in avatar")
    avatar_color: Optional[str] = Field(None, max_length=30)
    location: Optional[str] = Field(None, max_length=100, description="City, State, e.g. 'Austin, TX'")

    rating: int = Field(..., ge=1, le=5, description="Star rating 1–5")
    headline: str = Field(..., min_length=5, max_length=250, description="Short punchy headline")
    body: str = Field(..., min_length=20, max_length=2000, description="Full review text")

    highlight_metric: Optional[str] = Field(None, max_length=50, description="e.g. '9.2% cap rate'")
    highlight_label: Optional[str] = Field(None, max_length=100, description="e.g. 'Deal Found'")

    source: str = Field("platform", description="platform | google | trustpilot | linkedin | imported")

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        valid = {"platform", "google", "trustpilot", "linkedin", "imported"}
        if v not in valid:
            raise ValueError(f"source must be one of {valid}")
        return v


# ── Review Response ────────────────────────────────────────────────────────────
class ReviewResponse(BaseModel):
    """Full review response returned by the API."""

    model_config = {"from_attributes": True}

    id: int
    reviewer_name: str
    reviewer_title: Optional[str] = None
    reviewer_company: Optional[str] = None
    avatar_initials: str
    avatar_color: Optional[str] = None
    location: Optional[str] = None

    rating: int
    headline: str
    body: str

    highlight_metric: Optional[str] = None
    highlight_label: Optional[str] = None

    is_featured: bool
    source: str
    verified: bool
    helpful_count: int

    created_at: datetime
    updated_at: datetime


# ── Review Summary ─────────────────────────────────────────────────────────────
class ReviewSummary(BaseModel):
    """Aggregate statistics for all platform reviews."""

    total_reviews: int
    avg_rating: Optional[float] = Field(None, description="Average star rating (1–5)")
    avg_rating_formatted: Optional[str] = None      # "4.8"
    rating_distribution: dict[str, int]             # "5": 42, "4": 12, ...
    five_star_pct: Optional[float] = None           # Fraction of 5-star reviews
    five_star_pct_formatted: Optional[str] = None   # "84%"
    featured_count: int
    verified_count: int
    total_helpful: int


# ── Mark Helpful Request ───────────────────────────────────────────────────────
class MarkHelpfulResponse(BaseModel):
    """Response after marking a review as helpful."""
    success: bool
    review_id: int
    helpful_count: int
