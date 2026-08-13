"""Pydantic schemas for Property request/response validation."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ── Enums (as string literals for simplicity) ─────────────────────────────────
PROPERTY_TYPES = ["apartment", "condo", "townhouse", "single_family", "multi_family"]
SORT_FIELDS = ["list_price", "cap_rate", "rental_yield", "match_score", "days_on_market", "created_at"]
SORT_ORDERS = ["asc", "desc"]


# ── Investment Analytics Sub-Schema ──────────────────────────────────────────
class InvestmentMetrics(BaseModel):
    """Investment analytics computed for a property."""

    cap_rate: Optional[float] = Field(None, description="Capitalization rate (e.g., 0.084 = 8.4%)")
    cap_rate_pct: Optional[str] = Field(None, description="Human-readable cap rate (e.g., '8.4%')")

    rental_yield: Optional[float] = Field(None, description="Gross rental yield")
    rental_yield_pct: Optional[str] = None

    monthly_rent_estimate: Optional[float] = Field(None, description="Estimated monthly rent in USD")
    annual_rent_estimate: Optional[float] = None

    five_year_appreciation: Optional[float] = None
    yoy_growth: Optional[float] = None
    yoy_growth_pct: Optional[str] = None

    risk_score: Optional[int] = Field(None, ge=0, le=100, description="0=safe, 100=high risk")
    risk_label: Optional[str] = None   # "Low Risk", "Medium Risk", "High Risk"

    vacancy_rate: Optional[float] = None
    price_per_sqft: Optional[float] = None
    fair_value_estimate: Optional[float] = None
    value_vs_list_pct: Optional[str] = None  # e.g., "Undervalued by 4%"


# ── Property Response ────────────────────────────────────────────────────────
class PropertyResponse(BaseModel):
    """Full property response returned by the API."""

    model_config = {"from_attributes": True}

    id: int
    address: str
    city: str
    state: str
    zip_code: str
    neighborhood: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    bedrooms: int
    bathrooms: float
    square_feet: int
    property_type: str
    year_built: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

    list_price: float
    list_price_formatted: str = ""  # "$1,245,000"

    is_active: bool
    days_on_market: int

    metrics: InvestmentMetrics = InvestmentMetrics()

    # Computed by the scoring service when a search profile is provided
    match_score: Optional[int] = Field(None, ge=0, le=100)
    match_label: Optional[str] = None  # "Excellent Match", "Good Match", etc.

    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_with_metrics(cls, prop) -> "PropertyResponse":
        """Build a full response including computed metrics from an ORM Property."""
        from app.utils.scoring import risk_label, format_pct

        metrics = InvestmentMetrics(
            cap_rate=prop.cap_rate,
            cap_rate_pct=format_pct(prop.cap_rate),
            rental_yield=prop.rental_yield,
            rental_yield_pct=format_pct(prop.rental_yield),
            monthly_rent_estimate=prop.monthly_rent_estimate,
            annual_rent_estimate=(
                round(prop.monthly_rent_estimate * 12) if prop.monthly_rent_estimate else None
            ),
            five_year_appreciation=prop.five_year_appreciation,
            yoy_growth=prop.yoy_growth,
            yoy_growth_pct=format_pct(prop.yoy_growth),
            risk_score=prop.risk_score,
            risk_label=risk_label(prop.risk_score),
            vacancy_rate=prop.vacancy_rate,
            price_per_sqft=prop.price_per_sqft,
            fair_value_estimate=prop.fair_value_estimate,
            value_vs_list_pct=_value_vs_list(prop.fair_value_estimate, prop.list_price),
        )

        return cls(
            id=prop.id,
            address=prop.address,
            city=prop.city,
            state=prop.state,
            zip_code=prop.zip_code,
            neighborhood=prop.neighborhood,
            latitude=prop.latitude,
            longitude=prop.longitude,
            bedrooms=prop.bedrooms,
            bathrooms=prop.bathrooms,
            square_feet=prop.square_feet,
            property_type=prop.property_type,
            year_built=prop.year_built,
            description=prop.description,
            image_url=prop.image_url,
            list_price=prop.list_price,
            list_price_formatted=f"${prop.list_price:,.0f}",
            is_active=prop.is_active,
            days_on_market=prop.days_on_market,
            metrics=metrics,
            created_at=prop.created_at,
            updated_at=prop.updated_at,
        )


def _value_vs_list(fair_value: Optional[float], list_price: float) -> Optional[str]:
    if not fair_value or not list_price:
        return None
    diff_pct = ((fair_value - list_price) / list_price) * 100
    if abs(diff_pct) < 1:
        return "At fair value"
    direction = "Undervalued" if diff_pct > 0 else "Overvalued"
    return f"{direction} by {abs(diff_pct):.1f}%"


# ── Property Search / Filter Query ────────────────────────────────────────────
class PropertySearchParams(BaseModel):
    """Query parameters for property search and filtering."""

    # Location filters
    city: Optional[str] = Field(None, description="Filter by city name (case-insensitive partial match)")
    state: Optional[str] = Field(None, description="Filter by state abbreviation (e.g. 'TX')")
    zip_code: Optional[str] = None

    # Property filters
    property_type: Optional[str] = Field(None, description=f"One of: {PROPERTY_TYPES}")
    bedrooms: Optional[int] = Field(None, ge=0, le=20)
    min_bedrooms: Optional[int] = Field(None, ge=0)
    max_bedrooms: Optional[int] = Field(None, le=20)
    bathrooms: Optional[float] = None

    # Price range
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)

    # Investment metrics filters
    min_cap_rate: Optional[float] = Field(None, ge=0, le=1, description="Min cap rate as decimal (e.g. 0.08 = 8%)")
    max_cap_rate: Optional[float] = Field(None, ge=0, le=1)
    min_yield: Optional[float] = Field(None, ge=0, le=1, description="Min rental yield as decimal")
    max_risk_score: Optional[int] = Field(None, ge=0, le=100, description="Max risk score (0=safe)")
    min_yoy_growth: Optional[float] = Field(None, description="Min YoY growth as decimal")

    # Square footage
    min_sqft: Optional[int] = Field(None, ge=0)
    max_sqft: Optional[int] = None

    # Status
    is_active: Optional[bool] = Field(True, description="Show only active listings by default")

    # Pagination
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    # Sorting
    sort_by: str = Field("created_at", description=f"Sort field: {SORT_FIELDS}")
    sort_order: str = Field("desc", description="'asc' or 'desc'")

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        if v not in SORT_FIELDS:
            raise ValueError(f"sort_by must be one of {SORT_FIELDS}")
        return v

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        if v not in SORT_ORDERS:
            raise ValueError(f"sort_order must be 'asc' or 'desc'")
        return v


# ── Match Request ─────────────────────────────────────────────────────────────
class MatchRequest(BaseModel):
    """
    Investor profile used to compute AI match scores.
    POST /api/v1/properties/match
    """

    # Location preferences
    preferred_cities: List[str] = Field(default_factory=list)
    preferred_states: List[str] = Field(default_factory=list)

    # Property preferences
    preferred_property_types: List[str] = Field(default_factory=list)
    min_bedrooms: Optional[int] = Field(None, ge=0)
    max_bedrooms: Optional[int] = Field(None, le=20)

    # Budget
    max_budget: Optional[float] = Field(None, ge=0)
    min_budget: Optional[float] = Field(None, ge=0)

    # Investment goals (0.0–1.0 weighting for each criterion)
    target_cap_rate: Optional[float] = Field(None, ge=0, le=1)
    target_yield: Optional[float] = Field(None, ge=0, le=1)
    max_risk_score: Optional[int] = Field(50, ge=0, le=100)

    # How many results to return
    limit: int = Field(10, ge=1, le=50)


# ── Waitlist Schema ────────────────────────────────────────────────────────────
class WaitlistCreate(BaseModel):
    """Request body for joining the waitlist."""

    email: str = Field(..., description="Email address")
    source: str = Field("landing_page", description="Where the signup came from")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v


class WaitlistResponse(BaseModel):
    """Response after joining the waitlist."""

    success: bool
    message: str
    email: str
    position: Optional[int] = None
