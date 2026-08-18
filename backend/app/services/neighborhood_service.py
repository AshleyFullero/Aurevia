"""
Neighborhood Service
─────────────────────
Business logic for neighborhood intelligence retrieval and ranking.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.neighborhood import Neighborhood


class NeighborhoodService:
    """Business logic for neighborhood livability intelligence."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── List All / Filter ──────────────────────────────────────────────────────
    async def list_neighborhoods(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        min_livability: Optional[int] = None,
        min_walk_score: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Neighborhood], int]:
        """Return a paginated list of neighborhoods with optional filters."""
        stmt = select(Neighborhood)

        if city:
            stmt = stmt.where(Neighborhood.city.ilike(f"%{city}%"))
        if state:
            stmt = stmt.where(Neighborhood.state.ilike(f"%{state}%"))
        if min_livability is not None:
            stmt = stmt.where(Neighborhood.livability_score >= min_livability)
        if min_walk_score is not None:
            stmt = stmt.where(Neighborhood.walk_score >= min_walk_score)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = (
            stmt
            .order_by(Neighborhood.livability_score.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all(), total

    # ── Get Single ─────────────────────────────────────────────────────────────
    async def get_by_id(self, neighborhood_id: int) -> Optional[Neighborhood]:
        result = await self.db.execute(
            select(Neighborhood).where(Neighborhood.id == neighborhood_id)
        )
        return result.scalar_one_or_none()

    # ── Get by City (ranked) ───────────────────────────────────────────────────
    async def get_by_city(
        self,
        city: str,
        state: Optional[str] = None,
    ) -> tuple[str, str, List[Neighborhood]]:
        """
        Return all neighborhoods for a city ranked by livability_score descending.
        Returns (city, state, neighborhoods).
        """
        stmt = select(Neighborhood).where(Neighborhood.city.ilike(f"%{city}%"))
        if state:
            stmt = stmt.where(Neighborhood.state.ilike(f"%{state}%"))
        stmt = stmt.order_by(Neighborhood.livability_score.desc())

        result = await self.db.execute(stmt)
        neighborhoods = result.scalars().all()

        actual_city = neighborhoods[0].city if neighborhoods else city
        actual_state = neighborhoods[0].state if neighborhoods else (state or "")
        return actual_city, actual_state, neighborhoods

    # ── City Comparison ────────────────────────────────────────────────────────
    async def get_city_averages(self) -> List[Dict[str, Any]]:
        """
        Return average livability scores aggregated per city.
        Useful for city-level comparison widgets.
        """
        stmt = (
            select(
                Neighborhood.city,
                Neighborhood.state,
                func.count(Neighborhood.id).label("neighborhood_count"),
                func.avg(Neighborhood.livability_score).label("avg_livability"),
                func.avg(Neighborhood.walk_score).label("avg_walk"),
                func.avg(Neighborhood.transit_score).label("avg_transit"),
                func.avg(Neighborhood.school_rating).label("avg_school"),
                func.avg(Neighborhood.crime_index).label("avg_crime"),
            )
            .group_by(Neighborhood.city, Neighborhood.state)
            .order_by(func.avg(Neighborhood.livability_score).desc())
        )
        result = await self.db.execute(stmt)

        summaries = []
        for row in result.all():
            summaries.append({
                "city": row.city,
                "state": row.state,
                "market": f"{row.city}, {row.state}",
                "neighborhood_count": row.neighborhood_count,
                "avg_livability_score": round(row.avg_livability) if row.avg_livability else None,
                "avg_walk_score": round(row.avg_walk) if row.avg_walk else None,
                "avg_transit_score": round(row.avg_transit) if row.avg_transit else None,
                "avg_school_rating": round(row.avg_school, 1) if row.avg_school else None,
                "avg_crime_index": round(row.avg_crime) if row.avg_crime else None,
            })
        return summaries

    # ── Compute Livability Score (utility) ─────────────────────────────────────
    @staticmethod
    def compute_livability(n: Neighborhood) -> int:
        """
        Compute a composite 0–100 livability score from component metrics.
        Weights: Walk 25%, Transit 15%, Bike 5%, School 25%, Crime(inverted) 20%, Income 10%
        """
        score = 0.0
        weight_total = 0.0

        def _add(value: Optional[float], weight: float, invert: bool = False) -> None:
            nonlocal score, weight_total
            if value is not None:
                v = (100 - value) if invert else value
                score += v * weight
                weight_total += weight

        _add(n.walk_score, 0.25)
        _add(n.transit_score, 0.15)
        _add(n.bike_score, 0.05)
        _add(n.school_rating * 10 if n.school_rating else None, 0.25)  # scale 1-10 → 10-100
        _add(n.crime_index, 0.20, invert=True)

        # Median income: normalize to a 0–100 score (cap at $200K)
        if n.median_household_income:
            inc_score = min(100, (n.median_household_income / 200_000) * 100)
            _add(inc_score, 0.10)

        if weight_total == 0:
            return 50  # Default neutral score
        return int(round(score / weight_total))
