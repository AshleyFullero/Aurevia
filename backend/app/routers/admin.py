"""
Admin Router
────────────
Internal administration endpoints — no authentication for MVP.
Add JWT/API-key middleware before any production deployment.

Endpoints:
  GET /api/v1/admin/overview      — Combined dashboard stats
  GET /api/v1/admin/properties    — All properties (including inactive)
  GET /api/v1/admin/waitlist      — Full waitlist with emails + timestamps
  GET /api/v1/admin/contacts      — All contact form submissions
  PUT /api/v1/admin/properties/{id}/toggle — Toggle property active status
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contact import ContactSubmission
from app.models.property import Property
from app.models.waitlist import WaitlistEntry

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class WaitlistEntryOut(BaseModel):
    """Full waitlist entry for admin display."""
    model_config = {"from_attributes": True}
    id: int
    email: str
    source: str
    created_at: Any


class ContactOut(BaseModel):
    """Full contact submission for admin display."""
    model_config = {"from_attributes": True}
    id: int
    name: str
    email: str
    company: Optional[str]
    message: str
    source: str
    page_url: Optional[str]
    created_at: Any


class PropertyAdminOut(BaseModel):
    """Compact property row for admin listing."""
    model_config = {"from_attributes": True}
    id: int
    address: str
    city: str
    state: str
    property_type: str
    bedrooms: int
    list_price: float
    cap_rate: Optional[float]
    risk_score: Optional[int]
    is_active: bool
    days_on_market: int
    created_at: Any


class ToggleResponse(BaseModel):
    success: bool
    property_id: int
    is_active: bool
    message: str


# ── GET /admin/overview ───────────────────────────────────────────────────────

@router.get(
    "/overview",
    response_model=Dict[str, Any],
    summary="Admin dashboard overview",
    description=(
        "Returns a combined dashboard for internal admin use: total properties "
        "(active + inactive), waitlist count, contact form count, and breakdowns "
        "by property type and city."
    ),
)
async def admin_overview(db: AsyncSession = Depends(get_db)):
    """Return combined platform stats for the admin dashboard."""

    # Total properties (all, including inactive)
    total_props = (await db.execute(select(func.count(Property.id)))).scalar_one()
    active_props = (
        await db.execute(select(func.count(Property.id)).where(Property.is_active == True))
    ).scalar_one()
    inactive_props = total_props - active_props

    # Waitlist
    waitlist_count = (await db.execute(select(func.count(WaitlistEntry.id)))).scalar_one()

    # Contacts
    contact_count = (await db.execute(select(func.count(ContactSubmission.id)))).scalar_one()

    # Breakdown by city
    city_rows = await db.execute(
        select(Property.city, Property.state, func.count(Property.id).label("count"))
        .group_by(Property.city, Property.state)
        .order_by(func.count(Property.id).desc())
    )
    cities = [
        {"city": r.city, "state": r.state, "count": r.count}
        for r in city_rows.all()
    ]

    # Breakdown by property type
    type_rows = await db.execute(
        select(Property.property_type, func.count(Property.id).label("count"))
        .group_by(Property.property_type)
        .order_by(func.count(Property.id).desc())
    )
    by_type = [{"type": r.property_type, "count": r.count} for r in type_rows.all()]

    # Avg investment metrics (active only)
    metrics = await db.execute(
        select(
            func.avg(Property.cap_rate).label("avg_cap_rate"),
            func.avg(Property.rental_yield).label("avg_yield"),
            func.avg(Property.risk_score).label("avg_risk"),
            func.avg(Property.list_price).label("avg_price"),
        ).where(Property.is_active == True)
    )
    m = metrics.one()

    return {
        "total_properties": total_props,
        "active_properties": active_props,
        "inactive_properties": inactive_props,
        "waitlist_count": waitlist_count,
        "contact_count": contact_count,
        "by_city": cities,
        "by_property_type": by_type,
        "avg_cap_rate": round(m.avg_cap_rate, 4) if m.avg_cap_rate else None,
        "avg_cap_rate_pct": f"{m.avg_cap_rate * 100:.1f}%" if m.avg_cap_rate else None,
        "avg_yield": round(m.avg_yield, 4) if m.avg_yield else None,
        "avg_risk_score": round(m.avg_risk) if m.avg_risk else None,
        "avg_price": round(m.avg_price) if m.avg_price else None,
        "avg_price_formatted": f"${m.avg_price:,.0f}" if m.avg_price else None,
    }


# ── GET /admin/properties ─────────────────────────────────────────────────────

@router.get(
    "/properties",
    response_model=List[PropertyAdminOut],
    summary="List all properties (admin)",
    description=(
        "Returns all properties including inactive ones. Supports filtering by "
        "is_active and pagination."
    ),
)
async def admin_list_properties(
    is_active: Optional[bool] = Query(None, description="Filter by active/inactive status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Admin: list all properties with optional status filter."""
    stmt = select(Property).order_by(Property.created_at.desc())
    if is_active is not None:
        stmt = stmt.where(Property.is_active == is_active)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    return result.scalars().all()


# ── GET /admin/waitlist ───────────────────────────────────────────────────────

@router.get(
    "/waitlist",
    response_model=List[WaitlistEntryOut],
    summary="List all waitlist entries (admin)",
    description="Returns all waitlist entries sorted by signup date (newest first).",
)
async def admin_list_waitlist(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Admin: list all waitlist entries."""
    result = await db.execute(
        select(WaitlistEntry)
        .order_by(WaitlistEntry.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return result.scalars().all()


# ── GET /admin/contacts ───────────────────────────────────────────────────────

@router.get(
    "/contacts",
    response_model=List[ContactOut],
    summary="List all contact submissions (admin)",
    description="Returns all contact/demo-request form submissions sorted newest first.",
)
async def admin_list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Admin: list all contact form submissions."""
    result = await db.execute(
        select(ContactSubmission)
        .order_by(ContactSubmission.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return result.scalars().all()


# ── PUT /admin/properties/{id}/toggle ─────────────────────────────────────────

@router.put(
    "/properties/{property_id}/toggle",
    response_model=ToggleResponse,
    summary="Toggle property active status (admin)",
    description="Activate or deactivate a property listing without deleting it.",
)
async def toggle_property_status(
    property_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Admin: flip a property's is_active flag."""
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} not found.",
        )

    prop.is_active = not prop.is_active
    await db.commit()
    await db.refresh(prop)

    action = "activated" if prop.is_active else "deactivated"
    return ToggleResponse(
        success=True,
        property_id=property_id,
        is_active=prop.is_active,
        message=f"Property {property_id} {action} successfully.",
    )
