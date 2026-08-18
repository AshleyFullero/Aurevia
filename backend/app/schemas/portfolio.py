"""Pydantic schemas for Portfolio Tracker request/response validation."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.property import PropertyResponse


# ── Portfolio Entry Create ─────────────────────────────────────────────────────
class PortfolioEntryCreate(BaseModel):
    """Request body to add a property to the investor's portfolio."""

    property_id: int = Field(..., ge=1, description="ID of the property to track")

    purchase_price: Optional[float] = Field(
        None, ge=0, description="Actual purchase price (defaults to list price)"
    )
    purchase_date: Optional[date] = Field(
        None, description="Date of acquisition (YYYY-MM-DD)"
    )
    down_payment_pct: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Down payment as decimal, e.g. 0.20 = 20%"
    )
    mortgage_rate: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Annual mortgage rate as decimal, e.g. 0.065 = 6.5%"
    )
    loan_term_years: Optional[int] = Field(
        None, ge=1, le=50, description="Loan term in years, e.g. 30"
    )
    actual_monthly_rent: Optional[float] = Field(
        None, ge=0, description="Actual monthly rent received (overrides estimate)"
    )
    notes: Optional[str] = Field(None, max_length=2000)
    status: str = Field("active", description="active | sold | under_contract | watchlist")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = {"active", "sold", "under_contract", "watchlist"}
        if v not in valid:
            raise ValueError(f"status must be one of {valid}")
        return v


# ── Portfolio Entry Update ─────────────────────────────────────────────────────
class PortfolioEntryUpdate(BaseModel):
    """Partial update for a portfolio entry."""

    purchase_price: Optional[float] = Field(None, ge=0)
    purchase_date: Optional[date] = None
    down_payment_pct: Optional[float] = Field(None, ge=0.0, le=1.0)
    mortgage_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    loan_term_years: Optional[int] = Field(None, ge=1, le=50)
    actual_monthly_rent: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = {"active", "sold", "under_contract", "watchlist"}
        if v not in valid:
            raise ValueError(f"status must be one of {valid}")
        return v


# ── Portfolio Entry Response ───────────────────────────────────────────────────
class PortfolioEntryResponse(BaseModel):
    """Full portfolio entry with embedded property detail."""

    model_config = {"from_attributes": True}

    id: int
    property_id: int
    session_token: str

    purchase_price: Optional[float] = None
    purchase_date: Optional[date] = None
    down_payment_pct: Optional[float] = None
    mortgage_rate: Optional[float] = None
    loan_term_years: Optional[int] = None
    actual_monthly_rent: Optional[float] = None
    notes: Optional[str] = None
    status: str

    # Computed on-the-fly by the service layer
    equity_estimate: Optional[float] = None
    equity_formatted: Optional[str] = None
    monthly_mortgage_payment: Optional[float] = None
    monthly_cash_flow: Optional[float] = None
    monthly_cash_flow_formatted: Optional[str] = None
    cash_on_cash_return: Optional[float] = None
    cash_on_cash_pct: Optional[str] = None

    # Embedded property data
    property: Optional[PropertyResponse] = None

    created_at: datetime
    updated_at: datetime


# ── Portfolio Summary ──────────────────────────────────────────────────────────
class PortfolioSummary(BaseModel):
    """Aggregate statistics for the full session portfolio."""

    session_token: str
    total_entries: int
    active_entries: int

    # Value metrics
    total_portfolio_value: Optional[float] = None
    total_portfolio_value_formatted: Optional[str] = None

    total_purchase_cost: Optional[float] = None
    total_equity_estimate: Optional[float] = None
    total_equity_formatted: Optional[str] = None

    # Income
    total_monthly_income: Optional[float] = None
    total_monthly_income_formatted: Optional[str] = None
    total_annual_income: Optional[float] = None
    total_annual_income_formatted: Optional[str] = None

    # Returns
    portfolio_avg_cap_rate: Optional[float] = None
    portfolio_avg_cap_rate_pct: Optional[str] = None
    portfolio_weighted_cash_on_cash: Optional[float] = None
    portfolio_weighted_cash_on_cash_pct: Optional[str] = None

    # Cash flow
    total_monthly_mortgage: Optional[float] = None
    total_monthly_cash_flow: Optional[float] = None
    total_monthly_cash_flow_formatted: Optional[str] = None

    # Risk
    avg_risk_score: Optional[float] = None
    risk_label: Optional[str] = None

    # Breakdown
    by_property_type: Optional[dict] = None
    by_city: Optional[dict] = None
