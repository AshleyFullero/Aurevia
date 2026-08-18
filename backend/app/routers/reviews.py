"""
Reviews Router
──────────────
Endpoints:
  GET  /api/v1/reviews              — List reviews (paginated, filterable)
  POST /api/v1/reviews              — Submit a new review
  GET  /api/v1/reviews/summary      — Aggregate rating statistics
  GET  /api/v1/reviews/{id}         — Single review detail
  POST /api/v1/reviews/{id}/helpful — Mark a review as helpful
"""

from __future__ import annotations

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.review import (
    MarkHelpfulResponse,
    ReviewCreate,
    ReviewResponse,
    ReviewSummary,
)
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])


# ── GET /reviews/summary ───────────────────────────────────────────────────────
# NOTE: Must be defined before /{id} to avoid route shadowing.

@router.get(
    "/summary",
    response_model=ReviewSummary,
    summary="Aggregate review statistics",
    description=(
        "Returns platform-wide review statistics: total count, average star "
        "rating, distribution across 1–5 stars, and percentage of 5-star reviews. "
        "Designed for the social-proof hero widget."
    ),
)
async def get_review_summary(db: AsyncSession = Depends(get_db)):
    """Return aggregate review stats for marketing/social-proof widgets."""
    service = ReviewService(db)
    return await service.get_summary()


# ── GET /reviews ───────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=PaginatedResponse[ReviewResponse],
    summary="List platform reviews",
    description=(
        "Returns a paginated list of investor reviews. Filter by featured status, "
        "minimum rating, or source. Results are ordered: featured first, then by "
        "helpful count, then recency."
    ),
)
async def list_reviews(
    featured_only: bool = Query(False, description="Return only featured (promoted) reviews"),
    min_rating: int = Query(1, ge=1, le=5, description="Minimum star rating to include"),
    source: Optional[str] = Query(
        None,
        description="Filter by source: platform | google | trustpilot | linkedin | imported",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List reviews with optional filters."""
    service = ReviewService(db)
    items, total = await service.list_reviews(
        featured_only=featured_only,
        min_rating=min_rating,
        source=source,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


# ── POST /reviews ──────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new review",
    description=(
        "Submit a new investor review or testimonial. All new reviews are "
        "unverified and not featured by default — admin must promote them. "
        "Supports structured highlight metrics for display cards."
    ),
)
async def create_review(
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new review submission."""
    service = ReviewService(db)
    review = await service.create(payload)
    return review


# ── GET /reviews/{id} ─────────────────────────────────────────────────────────

@router.get(
    "/{review_id}",
    response_model=ReviewResponse,
    summary="Get a single review by ID",
)
async def get_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single review by its ID."""
    service = ReviewService(db)
    review = await service.get_by_id(review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID {review_id} not found.",
        )
    return review


# ── POST /reviews/{id}/helpful ─────────────────────────────────────────────────

@router.post(
    "/{review_id}/helpful",
    response_model=MarkHelpfulResponse,
    summary="Mark a review as helpful",
    description="Increment the helpful count for a review. Used for the 'Was this helpful?' UI.",
)
async def mark_helpful(
    review_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Increment the helpful count for a review."""
    service = ReviewService(db)
    review = await service.mark_helpful(review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID {review_id} not found.",
        )
    return MarkHelpfulResponse(
        success=True,
        review_id=review_id,
        helpful_count=review.helpful_count,
    )
