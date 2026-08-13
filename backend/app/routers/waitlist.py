"""
Waitlist Router
────────────────
Endpoints:
  POST /api/v1/waitlist   — Join the Aurevia early-access waitlist
  GET  /api/v1/waitlist/count — Public waitlist size
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.waitlist import WaitlistEntry
from app.schemas.property import WaitlistCreate, WaitlistResponse

router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


@router.post(
    "",
    response_model=WaitlistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Join the early-access waitlist",
)
async def join_waitlist(
    payload: WaitlistCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add an email to the Aurevia early-access waitlist."""

    # Check if already registered
    existing = await db.execute(
        select(WaitlistEntry).where(WaitlistEntry.email == payload.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already on the waitlist.",
        )

    entry = WaitlistEntry(email=payload.email, source=payload.source)
    db.add(entry)

    try:
        await db.commit()
        await db.refresh(entry)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already on the waitlist.",
        )

    # Get position (count of entries created before this one + 1)
    count_result = await db.execute(
        select(func.count()).select_from(WaitlistEntry)
    )
    position = count_result.scalar_one()

    return WaitlistResponse(
        success=True,
        message="You're on the list! We'll be in touch soon.",
        email=entry.email,
        position=position,
    )


@router.get(
    "/count",
    summary="Get waitlist size (public)",
    response_model=dict,
)
async def get_waitlist_count(db: AsyncSession = Depends(get_db)):
    """Returns how many people are on the waitlist (public count, no emails)."""
    result = await db.execute(select(func.count()).select_from(WaitlistEntry))
    count = result.scalar_one()
    return {"count": count, "unit": "people on the waitlist"}
