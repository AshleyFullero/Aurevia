"""
Review Service
──────────────
Business logic for review retrieval, creation, and aggregation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewSummary


class ReviewService:
    """Business logic for investor reviews and testimonials."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── List Reviews ───────────────────────────────────────────────────────────
    async def list_reviews(
        self,
        featured_only: bool = False,
        min_rating: int = 1,
        source: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Review], int]:
        """
        Return a paginated list of reviews.
        Returns (items, total_count).
        """
        stmt = select(Review).where(Review.rating >= min_rating)

        if featured_only:
            stmt = stmt.where(Review.is_featured == True)
        if source:
            stmt = stmt.where(Review.source == source)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        # Paginate, order featured first then by helpful_count
        stmt = (
            stmt
            .order_by(Review.is_featured.desc(), Review.helpful_count.desc(), Review.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all(), total

    # ── Get Single Review ──────────────────────────────────────────────────────
    async def get_by_id(self, review_id: int) -> Optional[Review]:
        result = await self.db.execute(select(Review).where(Review.id == review_id))
        return result.scalar_one_or_none()

    # ── Create Review ──────────────────────────────────────────────────────────
    async def create(self, payload: ReviewCreate) -> Review:
        """Create a new review and persist it."""
        review = Review(
            reviewer_name=payload.reviewer_name,
            reviewer_title=payload.reviewer_title,
            reviewer_company=payload.reviewer_company,
            avatar_initials=payload.avatar_initials,
            avatar_color=payload.avatar_color,
            location=payload.location,
            rating=payload.rating,
            headline=payload.headline,
            body=payload.body,
            highlight_metric=payload.highlight_metric,
            highlight_label=payload.highlight_label,
            source=payload.source,
            is_featured=False,   # New reviews require admin promotion
            verified=False,
        )
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        return review

    # ── Mark Helpful ───────────────────────────────────────────────────────────
    async def mark_helpful(self, review_id: int) -> Optional[Review]:
        """Increment the helpful_count for a review."""
        review = await self.get_by_id(review_id)
        if review is None:
            return None
        review.helpful_count += 1
        await self.db.commit()
        await self.db.refresh(review)
        return review

    # ── Get Summary ────────────────────────────────────────────────────────────
    async def get_summary(self) -> ReviewSummary:
        """Return aggregate review statistics."""
        # Total count
        total = (await self.db.execute(select(func.count(Review.id)))).scalar_one()

        # Average rating
        avg_row = await self.db.execute(select(func.avg(Review.rating)))
        avg_rating: Optional[float] = avg_row.scalar_one()

        # Rating distribution
        dist_result = await self.db.execute(
            select(Review.rating, func.count(Review.id).label("cnt"))
            .group_by(Review.rating)
            .order_by(Review.rating.desc())
        )
        rating_distribution: dict[str, int] = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
        for row in dist_result.all():
            rating_distribution[str(row.rating)] = row.cnt

        # Featured count
        featured_count = (
            await self.db.execute(
                select(func.count(Review.id)).where(Review.is_featured == True)
            )
        ).scalar_one()

        # Verified count
        verified_count = (
            await self.db.execute(
                select(func.count(Review.id)).where(Review.verified == True)
            )
        ).scalar_one()

        # Total helpful count
        total_helpful_row = await self.db.execute(select(func.sum(Review.helpful_count)))
        total_helpful = total_helpful_row.scalar_one() or 0

        # Derived metrics
        five_star_count = rating_distribution.get("5", 0)
        five_star_pct = (five_star_count / total) if total > 0 else None

        return ReviewSummary(
            total_reviews=total,
            avg_rating=round(avg_rating, 2) if avg_rating else None,
            avg_rating_formatted=f"{avg_rating:.1f}" if avg_rating else None,
            rating_distribution=rating_distribution,
            five_star_pct=five_star_pct,
            five_star_pct_formatted=f"{five_star_pct * 100:.0f}%" if five_star_pct else None,
            featured_count=featured_count,
            verified_count=verified_count,
            total_helpful=total_helpful,
        )
