"""
Neighborhoods Router
─────────────────────
Endpoints:
  GET /api/v1/neighborhoods                  — List all neighborhoods (filterable)
  GET /api/v1/neighborhoods/city-averages    — City-level livability aggregates
  GET /api/v1/neighborhoods/city/{city}      — Ranked neighborhoods in a city
  GET /api/v1/neighborhoods/{id}             — Full neighborhood detail
"""

from __future__ import annotations

import math
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.neighborhood import (
    CityNeighborhoodRanking,
    NeighborhoodResponse,
    NeighborhoodSummary,
)
from app.services.neighborhood_service import NeighborhoodService

router = APIRouter(prefix="/neighborhoods", tags=["Neighborhoods"])


# ── GET /neighborhoods/city-averages ──────────────────────────────────────────
# NOTE: Must be defined before /{id} to avoid route shadowing.

@router.get(
    "/city-averages",
    response_model=List[dict],
    summary="City-level livability averages",
    description=(
        "Returns average livability, walk, transit, school, and crime scores "
        "aggregated per city. Useful for city-comparison widgets on the dashboard."
    ),
)
async def get_city_averages(db: AsyncSession = Depends(get_db)):
    """Return per-city aggregated livability scores for comparison widgets."""
    service = NeighborhoodService(db)
    return await service.get_city_averages()


# ── GET /neighborhoods/city/{city} ────────────────────────────────────────────

@router.get(
    "/city/{city}",
    response_model=CityNeighborhoodRanking,
    summary="Ranked neighborhoods in a city",
    description=(
        "Returns all neighborhoods for a given city ranked by livability score "
        "(highest first). Optionally filter by state abbreviation."
    ),
)
async def get_neighborhoods_by_city(
    city: str,
    state: Optional[str] = Query(None, description="State abbreviation, e.g. 'TX'"),
    db: AsyncSession = Depends(get_db),
):
    """Return neighborhoods within a city ranked by livability score."""
    service = NeighborhoodService(db)
    actual_city, actual_state, neighborhoods = await service.get_by_city(city, state)

    if not neighborhoods:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No neighborhoods found for city '{city}'.",
        )

    summaries = [
        NeighborhoodSummary(
            id=n.id,
            city=n.city,
            state=n.state,
            neighborhood_name=n.neighborhood_name,
            livability_score=n.livability_score,
            walk_score=n.walk_score,
            school_rating=n.school_rating,
            crime_label=n.crime_label,
            popularity_trend=n.popularity_trend,
        )
        for n in neighborhoods
    ]

    return CityNeighborhoodRanking(
        city=actual_city,
        state=actual_state,
        total=len(summaries),
        neighborhoods=summaries,
    )


# ── GET /neighborhoods ─────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=PaginatedResponse[NeighborhoodSummary],
    summary="List neighborhoods",
    description=(
        "Returns a paginated list of neighborhoods. Filter by city, state, "
        "minimum livability score, or minimum walk score. Ordered by livability "
        "score descending."
    ),
)
async def list_neighborhoods(
    city: Optional[str] = Query(None, description="Filter by city (partial match)"),
    state: Optional[str] = Query(None, description="Filter by state abbreviation"),
    min_livability: Optional[int] = Query(None, ge=0, le=100, description="Minimum livability score"),
    min_walk_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum walk score"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List and filter neighborhoods."""
    service = NeighborhoodService(db)
    items, total = await service.list_neighborhoods(
        city=city,
        state=state,
        min_livability=min_livability,
        min_walk_score=min_walk_score,
        page=page,
        page_size=page_size,
    )
    summaries = [
        NeighborhoodSummary(
            id=n.id,
            city=n.city,
            state=n.state,
            neighborhood_name=n.neighborhood_name,
            livability_score=n.livability_score,
            walk_score=n.walk_score,
            school_rating=n.school_rating,
            crime_label=n.crime_label,
            popularity_trend=n.popularity_trend,
        )
        for n in items
    ]
    return PaginatedResponse(
        items=summaries,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


# ── GET /neighborhoods/{id} ───────────────────────────────────────────────────

@router.get(
    "/{neighborhood_id}",
    response_model=NeighborhoodResponse,
    summary="Get neighborhood detail by ID",
    description=(
        "Returns full livability intelligence for a specific neighborhood: "
        "walk/transit/bike scores, school rating, crime index, demographics, "
        "amenity counts, and popularity trend."
    ),
)
async def get_neighborhood(
    neighborhood_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full neighborhood intelligence for a specific neighborhood."""
    service = NeighborhoodService(db)
    neighborhood = await service.get_by_id(neighborhood_id)
    if not neighborhood:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Neighborhood with ID {neighborhood_id} not found.",
        )
    return neighborhood
