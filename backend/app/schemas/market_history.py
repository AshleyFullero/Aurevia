"""Pydantic schemas for Market Price History request/response validation."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ── Single Data Point ─────────────────────────────────────────────────────────
class PriceHistoryPoint(BaseModel):
    """One month of aggregated market metrics for a city/property_type."""

    model_config = {"from_attributes": True}

    id: int
    city: str
    state: str
    property_type: str
    period: str                          # "YYYY-MM"

    avg_price: Optional[float] = None
    avg_price_formatted: Optional[str] = None   # "$485,000"
    median_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    price_per_sqft: Optional[float] = None

    transaction_count: Optional[int] = None
    days_on_market_avg: Optional[float] = None

    avg_cap_rate: Optional[float] = None
    avg_cap_rate_pct: Optional[str] = None       # "8.2%"
    avg_rental_yield: Optional[float] = None
    avg_rental_yield_pct: Optional[str] = None

    mom_price_change: Optional[float] = None
    mom_price_change_pct: Optional[str] = None   # "+1.2%"
    yoy_price_change: Optional[float] = None
    yoy_price_change_pct: Optional[str] = None


# ── Market History Response ───────────────────────────────────────────────────
class MarketHistoryResponse(BaseModel):
    """Time-series price history for a specific market."""

    city: str
    state: str
    property_type: str
    months: int
    data_points: List[PriceHistoryPoint]

    # Summary stats derived from the series
    latest_avg_price: Optional[float] = None
    latest_avg_price_formatted: Optional[str] = None
    period_high: Optional[float] = None
    period_low: Optional[float] = None
    overall_change_pct: Optional[str] = None     # Change from first to last data point


# ── Heatmap Entry ─────────────────────────────────────────────────────────────
class HeatmapEntry(BaseModel):
    """City-level aggregated score for map/heatmap widget rendering."""

    city: str
    state: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    avg_price: Optional[float] = None
    avg_price_formatted: Optional[str] = None
    avg_cap_rate: Optional[float] = None
    avg_cap_rate_pct: Optional[str] = None
    avg_yoy_change: Optional[float] = None
    investment_score: Optional[float] = None     # Composite 0–100 score
    investment_grade: Optional[str] = None       # "A+", "A", "B+", etc.
    listing_count: int = 0


# ── Forecast Point ─────────────────────────────────────────────────────────────
class ForecastPoint(BaseModel):
    """A single forecasted month."""

    period: str                          # "YYYY-MM"
    forecast_avg_price: float
    forecast_avg_price_formatted: str
    is_forecast: bool = True             # Always True for forecasts


# ── Market Forecast Response ───────────────────────────────────────────────────
class MarketForecastResponse(BaseModel):
    """6-month linear price forecast for a market."""

    city: str
    state: str
    property_type: str
    forecast_months: int
    trend_slope: Optional[float] = None          # $/month change
    trend_direction: Optional[str] = None        # "upward", "downward", "flat"
    historical: List[PriceHistoryPoint]
    forecast: List[ForecastPoint]
    disclaimer: str = (
        "Forecasts are based on linear trend extrapolation from recent "
        "historical data and are provided for informational purposes only. "
        "Past performance does not guarantee future results."
    )
