"""
Property Service
────────────────
All business logic for querying, filtering, and scoring properties.
Keeps database queries out of the router layer.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import Property
from app.schemas.property import (
    MatchRequest,
    PropertyResponse,
    PropertySearchParams,
)
from app.utils.scoring import compute_match_score, match_label


class PropertyService:
    """Data-access and business-logic layer for properties."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Internal: Build WHERE clause from search params ───────────────────────
    def _build_filters(self, params: PropertySearchParams):
        """Return a list of SQLAlchemy filter expressions."""
        filters = []

        if params.is_active is not None:
            filters.append(Property.is_active == params.is_active)

        if params.city:
            filters.append(Property.city.ilike(f"%{params.city}%"))

        if params.state:
            filters.append(Property.state.ilike(params.state))

        if params.zip_code:
            filters.append(Property.zip_code == params.zip_code)

        if params.property_type:
            filters.append(Property.property_type == params.property_type.lower())

        # Bedrooms (exact match takes priority over range)
        if params.bedrooms is not None:
            filters.append(Property.bedrooms == params.bedrooms)
        else:
            if params.min_bedrooms is not None:
                filters.append(Property.bedrooms >= params.min_bedrooms)
            if params.max_bedrooms is not None:
                filters.append(Property.bedrooms <= params.max_bedrooms)

        if params.bathrooms is not None:
            filters.append(Property.bathrooms == params.bathrooms)

        # Price range
        if params.min_price is not None:
            filters.append(Property.list_price >= params.min_price)
        if params.max_price is not None:
            filters.append(Property.list_price <= params.max_price)

        # Investment metrics
        if params.min_cap_rate is not None:
            filters.append(Property.cap_rate >= params.min_cap_rate)
        if params.max_cap_rate is not None:
            filters.append(Property.cap_rate <= params.max_cap_rate)

        if params.min_yield is not None:
            filters.append(Property.rental_yield >= params.min_yield)

        if params.max_risk_score is not None:
            filters.append(Property.risk_score <= params.max_risk_score)

        if params.min_yoy_growth is not None:
            filters.append(Property.yoy_growth >= params.min_yoy_growth)

        # Square footage
        if params.min_sqft is not None:
            filters.append(Property.square_feet >= params.min_sqft)
        if params.max_sqft is not None:
            filters.append(Property.square_feet <= params.max_sqft)

        return filters

    def _get_sort_column(self, sort_by: str):
        """Map sort_by field name to SQLAlchemy column."""
        mapping = {
            "list_price":     Property.list_price,
            "cap_rate":       Property.cap_rate,
            "rental_yield":   Property.rental_yield,
            "days_on_market": Property.days_on_market,
            "created_at":     Property.created_at,
            # match_score is computed in Python, not in DB
        }
        return mapping.get(sort_by, Property.created_at)

    # ── Search ─────────────────────────────────────────────────────────────────
    async def search(
        self, params: PropertySearchParams
    ) -> Tuple[List[PropertyResponse], int]:
        """
        Search and filter properties.
        Returns (list_of_responses, total_count).
        """
        filters = self._build_filters(params)

        # Count total matching rows
        count_stmt = select(func.count()).select_from(Property)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Build paginated query
        sort_col = self._get_sort_column(params.sort_by)
        order_fn = desc if params.sort_order == "desc" else asc
        offset = (params.page - 1) * params.page_size

        stmt = select(Property).order_by(order_fn(sort_col))
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.offset(offset).limit(params.page_size)

        result = await self.db.execute(stmt)
        properties = result.scalars().all()

        responses = [PropertyResponse.from_orm_with_metrics(p) for p in properties]
        return responses, total

    # ── Get Single Property ────────────────────────────────────────────────────
    async def get_by_id(self, property_id: int) -> Optional[PropertyResponse]:
        """Fetch a single property by ID."""
        stmt = select(Property).where(Property.id == property_id)
        result = await self.db.execute(stmt)
        prop = result.scalar_one_or_none()
        if prop is None:
            return None
        return PropertyResponse.from_orm_with_metrics(prop)

    # ── AI Match Scoring ──────────────────────────────────────────────────────
    async def compute_matches(
        self, profile: MatchRequest
    ) -> List[PropertyResponse]:
        """
        Score all active properties against an investor profile,
        return top-N sorted by match score descending.
        """
        # Fetch all active properties (no pagination here — we score all)
        stmt = select(Property).where(Property.is_active == True)

        # Pre-filter on hard constraints to reduce Python-side scoring work
        filters = []
        if profile.max_budget:
            filters.append(Property.list_price <= profile.max_budget)
        if profile.min_budget:
            filters.append(Property.list_price >= profile.min_budget)
        if profile.max_risk_score is not None:
            # Allow some slack so we can still rank near-misses
            filters.append(Property.risk_score <= profile.max_risk_score + 20)
        if filters:
            stmt = stmt.where(and_(*filters))

        result = await self.db.execute(stmt)
        properties = result.scalars().all()

        # Score each property
        scored: List[Tuple[int, Property]] = []
        for prop in properties:
            score = compute_match_score(prop, profile)
            scored.append((score, prop))

        # Sort by score descending, take top N
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[: profile.limit]

        # Build responses and attach match score/label
        responses = []
        for score, prop in top:
            resp = PropertyResponse.from_orm_with_metrics(prop)
            resp.match_score = score
            resp.match_label = match_label(score)
            responses.append(resp)

        return responses
