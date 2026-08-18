"""
Market Router
─────────────
Endpoints:
  GET /api/v1/market/history    — Monthly time-series price data per city
  GET /api/v1/market/heatmap    — City-level investment scores for map widgets
  GET /api/v1/market/forecast   — 6-month linear price forecast per market
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.market_history import (
    HeatmapEntry,
    MarketForecastResponse,
    MarketHistoryResponse,
)
from app.services.market_service import MarketService

router = APIRouter(prefix="/market", tags=["Market"])


# ── GET /market/history ───────────────────────────────────────────────────────

@router.get(
    "/history",
    response_model=MarketHistoryResponse,
    summary="Monthly price history for a market",
    description=(
        "Returns monthly aggregated price history for a city/property_type "
        "combination. Includes average price, median price, cap rate, rental "
        "yield, month-over-month and year-over-year changes. Filter by city, "
        "state, property type, and number of months to look back."
    ),
)
async def get_market_history(
    city: str = Query(..., description="City name, e.g. 'Austin'"),
    state: Optional[str] = Query(None, description="State abbreviation, e.g. 'TX'"),
    property_type: str = Query(
        "all",
        description="Property type filter: all | apartment | condo | townhouse | single_family | multi_family",
    ),
    months: int = Query(24, ge=3, le=60, description="Number of months of history to return"),
    db: AsyncSession = Depends(get_db),
):
    """Return time-series price history for a city."""
    service = MarketService(db)
    result = await service.get_history(
        city=city, state=state, property_type=property_type, months=months
    )
    if not result.data_points:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No price history found for '{city}'"
                + (f", {state}" if state else "")
                + f" (type: {property_type}). "
                "Try a different city or property type."
            ),
        )
    return result


# ── GET /market/heatmap ───────────────────────────────────────────────────────

@router.get(
    "/heatmap",
    response_model=List[HeatmapEntry],
    summary="City investment heatmap data",
    description=(
        "Returns city-level aggregated investment scores (cap rate, YoY growth, "
        "risk) with geographic coordinates for rendering a heatmap or choropleth "
        "map widget. Each city gets a composite 0–100 investment score and a "
        "letter grade (A+, A, B+, ...)."
    ),
)
async def get_heatmap(db: AsyncSession = Depends(get_db)):
    """Return city-level aggregated heatmap scores for all markets."""
    service = MarketService(db)
    return await service.get_heatmap()


# ── GET /market/forecast ──────────────────────────────────────────────────────

@router.get(
    "/forecast",
    response_model=MarketForecastResponse,
    summary="6-month price forecast for a market",
    description=(
        "Generates a simple linear trend forecast for the next N months based on "
        "historical price data. Returns both the historical data points and the "
        "forecast extension, along with trend direction (upward/downward/flat) "
        "and slope. Includes a disclaimer about forecast accuracy limitations."
    ),
)
async def get_market_forecast(
    city: str = Query(..., description="City name, e.g. 'Miami'"),
    state: Optional[str] = Query(None, description="State abbreviation, e.g. 'FL'"),
    property_type: str = Query(
        "all",
        description="Property type: all | apartment | condo | townhouse | single_family | multi_family",
    ),
    forecast_months: int = Query(6, ge=1, le=12, description="Number of months to forecast ahead"),
    history_months: int = Query(24, ge=6, le=60, description="Months of history to base the forecast on"),
    db: AsyncSession = Depends(get_db),
):
    """Return a linear price forecast for a market based on historical trends."""
    service = MarketService(db)
    result = await service.get_forecast(
        city=city,
        state=state,
        property_type=property_type,
        forecast_months=forecast_months,
        history_months=history_months,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Insufficient historical data to generate a forecast for '{city}'. "
                "At least 3 months of history are required."
            ),
        )
    return result
