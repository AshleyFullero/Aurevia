"""
Favorites Router
────────────────
Session-based property bookmarking — no user account required for MVP.
Clients send an X-Session-Token header (any string, typically a UUID they
generate and persist in localStorage).  When auth is added, swap
session_token for a real user FK.

Endpoints:
  POST   /api/v1/favorites                   — Add a property to favorites
  GET    /api/v1/favorites                   — List all favorited properties
  DELETE /api/v1/favorites/{property_id}     — Remove from favorites
  GET    /api/v1/favorites/count             — Count of favorites for a session
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.favorite import Favorite
from app.models.property import Property
from app.schemas.property import PropertyResponse

router = APIRouter(prefix="/favorites", tags=["Favorites"])

_DEFAULT_TOKEN = "anonymous"


# ── Schemas ───────────────────────────────────────────────────────────────────

class FavoriteCreate(BaseModel):
    """Request body to add a property to favorites."""
    property_id: int = Field(..., description="ID of the property to favorite", ge=1)


class FavoriteResponse(BaseModel):
    """Confirmation that a favorite was saved."""
    success: bool
    message: str
    property_id: int
    session_token: str


class FavoriteCountResponse(BaseModel):
    """Count of favorites for a session."""
    count: int
    session_token: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _token(x_session_token: str | None) -> str:
    """Normalise session token — fall back to 'anonymous' if absent."""
    if not x_session_token or not x_session_token.strip():
        return _DEFAULT_TOKEN
    return x_session_token.strip()[:128]


# ── POST /favorites ────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=FavoriteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a property to favorites",
    description=(
        "Save a property to the session's favorites list. Requires a property_id "
        "in the request body. Optionally supply X-Session-Token header to associate "
        "favorites with a client session (recommended: UUID from localStorage)."
    ),
)
async def add_favorite(
    payload: FavoriteCreate,
    x_session_token: str | None = Header(None, description="Client session identifier"),
    db: AsyncSession = Depends(get_db),
):
    """Add a property to the session's favorites."""
    token = _token(x_session_token)

    # Verify property exists
    prop_result = await db.execute(
        select(Property).where(Property.id == payload.property_id)
    )
    if not prop_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {payload.property_id} not found.",
        )

    fav = Favorite(session_token=token, property_id=payload.property_id)
    db.add(fav)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This property is already in your favorites.",
        )

    return FavoriteResponse(
        success=True,
        message="Property added to favorites.",
        property_id=payload.property_id,
        session_token=token,
    )


# ── GET /favorites ─────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=List[PropertyResponse],
    summary="List favorited properties",
    description=(
        "Returns the full property details for all properties the session has "
        "favorited, ordered by when they were favorited (most recent first). "
        "Provide X-Session-Token to retrieve session-specific favorites."
    ),
)
async def list_favorites(
    x_session_token: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all favorited properties for this session."""
    token = _token(x_session_token)

    stmt = (
        select(Property)
        .join(Favorite, Favorite.property_id == Property.id)
        .where(Favorite.session_token == token)
        .order_by(Favorite.created_at.desc())
    )
    result = await db.execute(stmt)
    properties = result.scalars().all()

    return [PropertyResponse.from_orm_with_metrics(p) for p in properties]


# ── GET /favorites/count ───────────────────────────────────────────────────────

@router.get(
    "/count",
    response_model=FavoriteCountResponse,
    summary="Get favorites count for a session",
)
async def count_favorites(
    x_session_token: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Return the number of properties favorited by this session."""
    from sqlalchemy import func
    token = _token(x_session_token)
    result = await db.execute(
        select(func.count(Favorite.id)).where(Favorite.session_token == token)
    )
    count = result.scalar_one()
    return FavoriteCountResponse(count=count, session_token=token)


# ── DELETE /favorites/{property_id} ───────────────────────────────────────────

@router.delete(
    "/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a property from favorites",
    description="Delete a specific property from the session's favorites list.",
)
async def remove_favorite(
    property_id: int,
    x_session_token: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Remove a property from favorites."""
    token = _token(x_session_token)

    result = await db.execute(
        select(Favorite).where(
            Favorite.session_token == token,
            Favorite.property_id == property_id,
        )
    )
    fav = result.scalar_one_or_none()
    if not fav:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found.",
        )

    await db.delete(fav)
    await db.commit()
    # 204 No Content — no response body
