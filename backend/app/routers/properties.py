"""
Properties Router
─────────────────
Endpoints:
  GET  /api/v1/properties          — Search & filter properties
  GET  /api/v1/properties/{id}     — Get single property detail
  POST /api/v1/properties/match    — AI match scoring
"""

from __future__ import annotations

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.property import (
    MatchRequest,
    PropertyResponse,
    PropertySearchParams,
)
from app.services.property_service import PropertyService

router = APIRouter(prefix="/properties", tags=["Properties"])


# ── GET /properties ────────────────────────────────────────────────────────────
@router.get(
    "",
    response_model=PaginatedResponse[PropertyResponse],
    summary="Search & filter properties",
    description=(
        "Search the Aurevia property database with flexible filters for location, "
        "price, bedrooms, investment metrics (cap rate, yield, risk), and more. "
        "Results are paginated and sortable."
    ),
)
async def search_properties(
    # Location
    city: Optional[str] = Query(None, description="City name (partial match)"),
    state: Optional[str] = Query(None, description="State abbreviation, e.g. 'TX'"),
    zip_code: Optional[str] = Query(None),
    # Property
    property_type: Optional[str] = Query(None, description="apartment|condo|townhouse|single_family|multi_family"),
    bedrooms: Optional[int] = Query(None, ge=0),
    min_bedrooms: Optional[int] = Query(None, ge=0),
    max_bedrooms: Optional[int] = Query(None, le=20),
    bathrooms: Optional[float] = Query(None, ge=0, description="Exact bathroom count, e.g. 2.0 or 2.5"),
    # Price
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    # Investment metrics
    min_cap_rate: Optional[float] = Query(None, ge=0, le=1, description="e.g. 0.08 for 8%"),
    max_cap_rate: Optional[float] = Query(None, ge=0, le=1),
    min_yield: Optional[float] = Query(None, ge=0, le=1, description="e.g. 0.06 for 6%"),
    max_risk_score: Optional[int] = Query(None, ge=0, le=100),
    min_yoy_growth: Optional[float] = Query(None),
    # Sqft
    min_sqft: Optional[int] = Query(None, ge=0),
    max_sqft: Optional[int] = Query(None),
    # Pagination & sort
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", description="list_price|cap_rate|rental_yield|days_on_market|created_at"),
    sort_order: str = Query("desc", description="asc|desc"),
    db: AsyncSession = Depends(get_db),
):
    params = PropertySearchParams(
        city=city, state=state, zip_code=zip_code,
        property_type=property_type, bedrooms=bedrooms,
        min_bedrooms=min_bedrooms, max_bedrooms=max_bedrooms,
        bathrooms=bathrooms,
        min_price=min_price, max_price=max_price,
        min_cap_rate=min_cap_rate, max_cap_rate=max_cap_rate,
        min_yield=min_yield, max_risk_score=max_risk_score,
        min_yoy_growth=min_yoy_growth,
        min_sqft=min_sqft, max_sqft=max_sqft,
        page=page, page_size=page_size,
        sort_by=sort_by, sort_order=sort_order,
    )

    service = PropertyService(db)
    items, total = await service.search(params)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


# ── POST /properties/match ─────────────────────────────────────────────────────
@router.post(
    "/match",
    response_model=list[PropertyResponse],
    summary="AI property match scoring",
    description=(
        "Submit an investor profile (budget, location preference, target cap rate/yield, "
        "risk tolerance) and receive properties ranked by AI match score (0–100)."
    ),
)
async def match_properties(
    profile: MatchRequest,
    db: AsyncSession = Depends(get_db),
):
    service = PropertyService(db)
    results = await service.compute_matches(profile)
    return results


# ── GET /properties/{id} ───────────────────────────────────────────────────────
@router.get(
    "/{property_id}",
    response_model=PropertyResponse,
    summary="Get property by ID",
)
async def get_property(
    property_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = PropertyService(db)
    prop = await service.get_by_id(property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found.",
        )
    return prop
