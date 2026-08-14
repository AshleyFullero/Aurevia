"""
Analytics Service
─────────────────
Computes market-level and property-level investment analytics.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import Property


class AnalyticsService:
    """Business logic for market and investment analytics."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_market_summary(self, city: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Return aggregated market metrics per city (or for a specific city).
        Used by: GET /api/v1/analytics/market
        """
        stmt = (
            select(
                Property.city,
                Property.state,
                func.count(Property.id).label("total_listings"),
                func.avg(Property.list_price).label("avg_price"),
                func.min(Property.list_price).label("min_price"),
                func.max(Property.list_price).label("max_price"),
                func.avg(Property.cap_rate).label("avg_cap_rate"),
                func.avg(Property.rental_yield).label("avg_yield"),
                func.avg(Property.yoy_growth).label("avg_yoy_growth"),
                func.avg(Property.risk_score).label("avg_risk_score"),
                func.avg(Property.vacancy_rate).label("avg_vacancy"),
                func.avg(Property.price_per_sqft).label("avg_price_per_sqft"),
            )
            .where(Property.is_active == True)
            .group_by(Property.city, Property.state)
            .order_by(func.count(Property.id).desc())
        )

        if city:
            stmt = stmt.where(Property.city.ilike(f"%{city}%"))

        result = await self.db.execute(stmt)
        rows = result.all()

        summaries = []
        for row in rows:
            summaries.append({
                "city": row.city,
                "state": row.state,
                "market": f"{row.city}, {row.state}",
                "total_listings": row.total_listings,
                "avg_price": round(row.avg_price) if row.avg_price else None,
                "avg_price_formatted": f"${row.avg_price:,.0f}" if row.avg_price else None,
                "min_price": round(row.min_price) if row.min_price else None,
                "max_price": round(row.max_price) if row.max_price else None,
                "avg_cap_rate": round(row.avg_cap_rate, 4) if row.avg_cap_rate else None,
                "avg_cap_rate_pct": f"{row.avg_cap_rate * 100:.1f}%" if row.avg_cap_rate else None,
                "avg_yield": round(row.avg_yield, 4) if row.avg_yield else None,
                "avg_yield_pct": f"{row.avg_yield * 100:.1f}%" if row.avg_yield else None,
                "avg_yoy_growth": round(row.avg_yoy_growth, 4) if row.avg_yoy_growth else None,
                "avg_yoy_growth_pct": f"{row.avg_yoy_growth * 100:.1f}%" if row.avg_yoy_growth else None,
                "avg_risk_score": round(row.avg_risk_score) if row.avg_risk_score else None,
                "avg_vacancy": round(row.avg_vacancy, 4) if row.avg_vacancy else None,
                "avg_vacancy_pct": f"{row.avg_vacancy * 100:.1f}%" if row.avg_vacancy else None,
                "avg_price_per_sqft": round(row.avg_price_per_sqft) if row.avg_price_per_sqft else None,
            })

        return summaries

    async def get_property_analytics(self, property_id: int) -> Optional[Dict[str, Any]]:
        """
        Return detailed investment analytics for a specific property.
        Used by: GET /api/v1/analytics/property/{id}
        """
        stmt = select(Property).where(Property.id == property_id)
        result = await self.db.execute(stmt)
        prop = result.scalar_one_or_none()

        if prop is None:
            return None

        # Compute annualised cash flow estimates
        annual_rent = (prop.monthly_rent_estimate or 0) * 12
        operating_expenses_est = annual_rent * 0.35  # 35% expense ratio estimate
        noi = annual_rent - operating_expenses_est  # Net Operating Income
        cash_on_cash = (noi / prop.list_price) if prop.list_price else None

        # IRR approximation (simplified 5-year hold)
        irr_est = None
        if prop.cap_rate and prop.five_year_appreciation:
            irr_est = round((prop.cap_rate + prop.five_year_appreciation / 5) * 100, 2)

        return {
            "property_id": prop.id,
            "address": prop.address,
            "city": prop.city,
            "state": prop.state,
            "list_price": prop.list_price,
            "list_price_formatted": f"${prop.list_price:,.0f}",
            "fair_value_estimate": prop.fair_value_estimate,

            # Rental income
            "monthly_rent_estimate": prop.monthly_rent_estimate,
            "annual_rent_estimate": round(annual_rent) if annual_rent else None,

            # Returns
            "cap_rate": prop.cap_rate,
            "cap_rate_pct": f"{prop.cap_rate * 100:.1f}%" if prop.cap_rate else None,
            "rental_yield": prop.rental_yield,
            "rental_yield_pct": f"{prop.rental_yield * 100:.1f}%" if prop.rental_yield else None,
            "cash_on_cash_return": round(cash_on_cash, 4) if cash_on_cash else None,
            "cash_on_cash_pct": f"{cash_on_cash * 100:.1f}%" if cash_on_cash else None,
            "irr_estimate_pct": f"{irr_est}%" if irr_est else None,

            # Growth
            "yoy_growth": prop.yoy_growth,
            "yoy_growth_pct": f"{prop.yoy_growth * 100:.1f}%" if prop.yoy_growth else None,
            "five_year_appreciation": prop.five_year_appreciation,
            "five_year_appreciation_pct": (
                f"{prop.five_year_appreciation * 100:.1f}%" if prop.five_year_appreciation else None
            ),

            # Risk
            "risk_score": prop.risk_score,
            "risk_label": _risk_label(prop.risk_score),
            "vacancy_rate": prop.vacancy_rate,
            "vacancy_pct": f"{prop.vacancy_rate * 100:.1f}%" if prop.vacancy_rate else None,

            # Per-sqft
            "price_per_sqft": prop.price_per_sqft,
        }


def _risk_label(score: Optional[int]) -> Optional[str]:
    if score is None:
        return None
    if score <= 30:
        return "Low Risk"
    if score <= 65:
        return "Medium Risk"
    return "High Risk"
