"""
Analytics Router
─────────────────
Endpoints:
  GET /api/v1/analytics/market               — Aggregated market stats per city
  GET /api/v1/analytics/property/{id}        — Investment analytics for one property
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ── GET /analytics/market ──────────────────────────────────────────────────────
@router.get(
    "/market",
    response_model=List[Dict[str, Any]],
    summary="Market-level analytics",
    description=(
        "Returns aggregated investment metrics per city — average price, "
        "cap rate, rental yield, year-over-year growth, vacancy, and risk score. "
        "Optionally filter by city name."
    ),
)
async def get_market_analytics(
    city: Optional[str] = Query(None, description="Filter by city name"),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_market_summary(city=city)


# ── GET /analytics/property/{id} ───────────────────────────────────────────────
@router.get(
    "/property/{property_id}",
    response_model=Dict[str, Any],
    summary="Per-property investment analytics",
    description=(
        "Returns detailed investment analytics for a single property: "
        "cap rate, rental yield, estimated NOI, cash-on-cash return, "
        "IRR estimate, appreciation, and risk assessment."
    ),
)
async def get_property_analytics(
    property_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    result = await service.get_property_analytics(property_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found.",
        )
    return result
