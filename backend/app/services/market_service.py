"""
Market Service
──────────────
Business logic for market price history trends, heatmaps, and forecasting.
"""

from __future__ import annotations

import statistics
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.neighborhood import Neighborhood
from app.models.price_history import PriceHistory
from app.models.property import Property
from app.schemas.market_history import (
    ForecastPoint,
    HeatmapEntry,
    MarketForecastResponse,
    MarketHistoryResponse,
    PriceHistoryPoint,
)


# ── City coordinates (for heatmap pins) ──────────────────────────────────────
_CITY_COORDS: Dict[str, Tuple[float, float]] = {
    "Austin":        (30.2672, -97.7431),
    "Miami":         (25.7617, -80.1918),
    "Denver":        (39.7392, -104.9903),
    "Nashville":     (36.1627, -86.7816),
    "Seattle":       (47.6062, -122.3321),
    "Phoenix":       (33.4484, -112.0740),
    "New York":      (40.7128, -74.0060),
    "Chicago":       (41.8781, -87.6298),
    "Boston":        (42.3601, -71.0589),
    "San Francisco": (37.7749, -122.4194),
    "Los Angeles":   (34.0522, -118.2437),
    "Dallas":        (32.7767, -96.7970),
    "Houston":       (29.7604, -95.3698),
    "Charlotte":     (35.2271, -80.8431),
    "Raleigh":       (35.7796, -78.6382),
}


class MarketService:
    """Business logic for market price history, heatmaps, and forecasting."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Price History ──────────────────────────────────────────────────────────
    async def get_history(
        self,
        city: str,
        state: Optional[str] = None,
        property_type: str = "all",
        months: int = 24,
    ) -> MarketHistoryResponse:
        """
        Return time-series price history for a city/property_type.
        """
        stmt = (
            select(PriceHistory)
            .where(
                PriceHistory.city.ilike(f"%{city}%"),
                PriceHistory.property_type == property_type,
            )
            .order_by(PriceHistory.period.asc())
        )
        if state:
            stmt = stmt.where(PriceHistory.state.ilike(f"%{state}%"))

        result = await self.db.execute(stmt)
        all_rows = result.scalars().all()

        # Take the most recent N months
        rows = all_rows[-months:] if len(all_rows) > months else all_rows

        data_points = [_row_to_point(r) for r in rows]

        # Summary stats
        prices = [r.avg_price for r in rows if r.avg_price]
        latest_price = prices[-1] if prices else None
        period_high = max(prices) if prices else None
        period_low = min(prices) if prices else None

        overall_change_pct: Optional[str] = None
        if len(prices) >= 2:
            change = (prices[-1] - prices[0]) / prices[0]
            sign = "+" if change >= 0 else ""
            overall_change_pct = f"{sign}{change * 100:.1f}%"

        actual_city = rows[0].city if rows else city
        actual_state = rows[0].state if rows else (state or "")

        return MarketHistoryResponse(
            city=actual_city,
            state=actual_state,
            property_type=property_type,
            months=len(data_points),
            data_points=data_points,
            latest_avg_price=latest_price,
            latest_avg_price_formatted=f"${latest_price:,.0f}" if latest_price else None,
            period_high=period_high,
            period_low=period_low,
            overall_change_pct=overall_change_pct,
        )

    # ── Heatmap ────────────────────────────────────────────────────────────────
    async def get_heatmap(self) -> List[HeatmapEntry]:
        """
        Return city-level aggregated investment scores for heatmap rendering.
        Combines live property data from the properties table.
        """
        stmt = (
            select(
                Property.city,
                Property.state,
                func.count(Property.id).label("listing_count"),
                func.avg(Property.list_price).label("avg_price"),
                func.avg(Property.cap_rate).label("avg_cap_rate"),
                func.avg(Property.yoy_growth).label("avg_yoy"),
                func.avg(Property.risk_score).label("avg_risk"),
                func.avg(Property.rental_yield).label("avg_yield"),
            )
            .where(Property.is_active == True)
            .group_by(Property.city, Property.state)
            .order_by(func.count(Property.id).desc())
        )
        result = await self.db.execute(stmt)

        entries = []
        for row in result.all():
            # Compute a composite investment score 0–100
            cap_score = min(100, (row.avg_cap_rate or 0) * 1000) if row.avg_cap_rate else 0
            growth_score = min(100, ((row.avg_yoy or 0) + 0.1) * 500) if row.avg_yoy else 50
            risk_score = max(0, 100 - (row.avg_risk or 50)) if row.avg_risk else 50
            investment_score = cap_score * 0.45 + growth_score * 0.30 + risk_score * 0.25

            grade = _investment_grade(investment_score)
            lat, lon = _CITY_COORDS.get(row.city, (None, None))

            entries.append(HeatmapEntry(
                city=row.city,
                state=row.state,
                latitude=lat,
                longitude=lon,
                avg_price=round(row.avg_price) if row.avg_price else None,
                avg_price_formatted=f"${row.avg_price:,.0f}" if row.avg_price else None,
                avg_cap_rate=round(row.avg_cap_rate, 4) if row.avg_cap_rate else None,
                avg_cap_rate_pct=f"{row.avg_cap_rate * 100:.1f}%" if row.avg_cap_rate else None,
                avg_yoy_change=round(row.avg_yoy, 4) if row.avg_yoy else None,
                investment_score=round(investment_score, 1),
                investment_grade=grade,
                listing_count=row.listing_count,
            ))

        return entries

    # ── Forecast ───────────────────────────────────────────────────────────────
    async def get_forecast(
        self,
        city: str,
        state: Optional[str] = None,
        property_type: str = "all",
        forecast_months: int = 6,
        history_months: int = 24,
    ) -> Optional[MarketForecastResponse]:
        """
        Generate a simple linear trend forecast for a market.
        Returns None if insufficient history data exists.
        """
        history = await self.get_history(city, state, property_type, history_months)

        valid_points = [
            (i, p.avg_price)
            for i, p in enumerate(history.data_points)
            if p.avg_price is not None
        ]

        if len(valid_points) < 3:
            return None

        # Simple linear regression (least-squares)
        n = len(valid_points)
        xs = [v[0] for v in valid_points]
        ys = [v[1] for v in valid_points]
        x_mean = statistics.mean(xs)
        y_mean = statistics.mean(ys)
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
        denominator = sum((x - x_mean) ** 2 for x in xs)
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean

        # Determine trend direction
        if slope > 500:
            trend_direction = "upward"
        elif slope < -500:
            trend_direction = "downward"
        else:
            trend_direction = "flat"

        # Build forecast points (continuing from last historical period)
        last_period = history.data_points[-1].period if history.data_points else "2024-12"
        last_year, last_month = map(int, last_period.split("-"))

        forecast_points: List[ForecastPoint] = []
        for i in range(1, forecast_months + 1):
            m = last_month + i
            y = last_year + (m - 1) // 12
            m = ((m - 1) % 12) + 1
            period_str = f"{y:04d}-{m:02d}"
            x_next = len(valid_points) - 1 + i
            price = max(0, slope * x_next + intercept)
            forecast_points.append(ForecastPoint(
                period=period_str,
                forecast_avg_price=round(price),
                forecast_avg_price_formatted=f"${price:,.0f}",
            ))

        return MarketForecastResponse(
            city=history.city,
            state=history.state,
            property_type=property_type,
            forecast_months=forecast_months,
            trend_slope=round(slope, 2),
            trend_direction=trend_direction,
            historical=history.data_points,
            forecast=forecast_points,
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _row_to_point(row: PriceHistory) -> PriceHistoryPoint:
    """Convert a PriceHistory ORM row to its Pydantic response schema."""
    return PriceHistoryPoint(
        id=row.id,
        city=row.city,
        state=row.state,
        property_type=row.property_type,
        period=row.period,
        avg_price=row.avg_price,
        avg_price_formatted=f"${row.avg_price:,.0f}" if row.avg_price else None,
        median_price=row.median_price,
        min_price=row.min_price,
        max_price=row.max_price,
        price_per_sqft=row.price_per_sqft,
        transaction_count=row.transaction_count,
        days_on_market_avg=row.days_on_market_avg,
        avg_cap_rate=row.avg_cap_rate,
        avg_cap_rate_pct=f"{row.avg_cap_rate * 100:.1f}%" if row.avg_cap_rate else None,
        avg_rental_yield=row.avg_rental_yield,
        avg_rental_yield_pct=f"{row.avg_rental_yield * 100:.1f}%" if row.avg_rental_yield else None,
        mom_price_change=row.mom_price_change,
        mom_price_change_pct=_fmt_change(row.mom_price_change),
        yoy_price_change=row.yoy_price_change,
        yoy_price_change_pct=_fmt_change(row.yoy_price_change),
    )


def _fmt_change(v: Optional[float]) -> Optional[str]:
    if v is None:
        return None
    sign = "+" if v >= 0 else ""
    return f"{sign}{v * 100:.1f}%"


def _investment_grade(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B+"
    if score >= 60:
        return "B"
    if score >= 50:
        return "C+"
    if score >= 40:
        return "C"
    return "D"
