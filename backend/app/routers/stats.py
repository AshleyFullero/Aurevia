"""
Stats Router
────────────
Endpoints:
  GET /api/v1/stats/overview   — Platform-wide aggregate statistics
  GET /api/v1/stats/markets    — Quick city market summary (for dashboard widgets)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.analytics_service import AnalyticsService
from app.services.stats_service import StatsService

router = APIRouter(prefix="/stats", tags=["Stats"])


# ── GET /stats/overview ───────────────────────────────────────────────────────

@router.get(
    "/overview",
    response_model=Dict[str, Any],
    summary="Platform overview statistics",
    description=(
        "Returns platform-wide aggregate statistics: total properties, markets "
        "covered, waitlist size, average cap rate, YoY growth, and total listing "
        "volume. Designed for the landing page stats bar and marketing widgets."
    ),
)
async def get_overview_stats(db: AsyncSession = Depends(get_db)):
    """Return platform KPIs for the marketing site stats bar."""
    service = StatsService(db)
    return await service.get_platform_stats()


# ── GET /stats/markets ────────────────────────────────────────────────────────

@router.get(
    "/markets",
    response_model=List[Dict[str, Any]],
    summary="Quick market summary for dashboard widgets",
    description=(
        "Returns the top N markets by listing count with key investment metrics. "
        "Lightweight version of /analytics/market — optimised for widget rendering. "
        "Optionally limit results with the 'limit' parameter."
    ),
)
async def get_market_widget(
    limit: int = Query(6, ge=1, le=20, description="Maximum number of markets to return"),
    db: AsyncSession = Depends(get_db),
):
    """Return top markets for dashboard/widget display."""
    service = AnalyticsService(db)
    all_markets = await service.get_market_summary()
    return all_markets[:limit]
