"""Pydantic schemas for Neighborhood intelligence request/response validation."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


# ── Neighborhood Response ──────────────────────────────────────────────────────
class NeighborhoodResponse(BaseModel):
    """Full neighborhood intelligence response."""

    model_config = {"from_attributes": True}

    id: int
    city: str
    state: str
    neighborhood_name: str
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Scores (0–100)
    walk_score: Optional[int] = None
    transit_score: Optional[int] = None
    bike_score: Optional[int] = None
    livability_score: Optional[int] = None

    # Education
    school_rating: Optional[float] = None
    school_count: Optional[int] = None

    # Safety
    crime_index: Optional[int] = None
    crime_label: Optional[str] = None

    # Demographics
    median_household_income: Optional[float] = None
    median_household_income_formatted: Optional[str] = None  # "$82,000"
    population_density: Optional[int] = None
    median_age: Optional[float] = None

    # Amenities
    restaurant_count: Optional[int] = None
    grocery_count: Optional[int] = None
    park_count: Optional[int] = None
    gym_count: Optional[int] = None
    hospital_distance_miles: Optional[float] = None
    top_amenities: Optional[List[str]] = None   # Parsed from JSON text

    # Trend
    popularity_trend: Optional[str] = None
    gentrification_risk: Optional[str] = None

    # Walk score labels
    walk_score_label: Optional[str] = None
    transit_score_label: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def compute_derived(self) -> "NeighborhoodResponse":
        """Compute human-readable labels and formatted fields."""
        if self.median_household_income:
            self.median_household_income_formatted = (
                f"${self.median_household_income:,.0f}"
            )
        if self.walk_score is not None:
            self.walk_score_label = _walk_label(self.walk_score)
        if self.transit_score is not None:
            self.transit_score_label = _transit_label(self.transit_score)
        # top_amenities is stored as a JSON string in the DB — parse it
        if isinstance(self.top_amenities, str):
            try:
                self.top_amenities = json.loads(self.top_amenities)
            except (json.JSONDecodeError, TypeError):
                self.top_amenities = []
        return self


# ── Neighborhood Summary (compact) ────────────────────────────────────────────
class NeighborhoodSummary(BaseModel):
    """Compact neighborhood card for listing views."""

    model_config = {"from_attributes": True}

    id: int
    city: str
    state: str
    neighborhood_name: str
    livability_score: Optional[int] = None
    walk_score: Optional[int] = None
    school_rating: Optional[float] = None
    crime_label: Optional[str] = None
    popularity_trend: Optional[str] = None


# ── City Neighborhood Ranking ──────────────────────────────────────────────────
class CityNeighborhoodRanking(BaseModel):
    """Ranked list of neighborhoods in a city."""
    city: str
    state: str
    total: int
    neighborhoods: List[NeighborhoodSummary]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _walk_label(score: int) -> str:
    if score >= 90:
        return "Walker's Paradise"
    if score >= 70:
        return "Very Walkable"
    if score >= 50:
        return "Somewhat Walkable"
    if score >= 25:
        return "Car-Friendly"
    return "Car-Dependent"


def _transit_label(score: int) -> str:
    if score >= 90:
        return "Rider's Paradise"
    if score >= 70:
        return "Excellent Transit"
    if score >= 50:
        return "Good Transit"
    if score >= 25:
        return "Some Transit"
    return "Minimal Transit"
