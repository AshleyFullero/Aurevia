"""
Portfolio Router
────────────────
Session-based investment portfolio tracking — no user account required for MVP.
Clients supply an X-Session-Token header (UUID from localStorage).

Endpoints:
  POST   /api/v1/portfolio              — Add a property to portfolio
  GET    /api/v1/portfolio              — List portfolio entries with financials
  GET    /api/v1/portfolio/summary      — Aggregate portfolio statistics
  PUT    /api/v1/portfolio/{id}         — Update a portfolio entry
  DELETE /api/v1/portfolio/{id}         — Remove a portfolio entry
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.portfolio import (
    PortfolioEntryCreate,
    PortfolioEntryUpdate,
    PortfolioSummary,
)
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

_DEFAULT_TOKEN = "anonymous"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _token(x_session_token: str | None) -> str:
    """Normalise session token — fall back to 'anonymous' if absent."""
    if not x_session_token or not x_session_token.strip():
        return _DEFAULT_TOKEN
    return x_session_token.strip()[:128]


# ── GET /portfolio/summary ─────────────────────────────────────────────────────
# NOTE: Must be defined before /{id} to avoid route shadowing.

@router.get(
    "/summary",
    response_model=PortfolioSummary,
    summary="Aggregate portfolio statistics",
    description=(
        "Returns aggregate financial statistics for the session's entire portfolio: "
        "total value, total equity, monthly income, average cap rate, cash-on-cash "
        "return, monthly mortgage payments, net cash flow, and breakdowns by "
        "property type and city."
    ),
)
async def get_portfolio_summary(
    x_session_token: str | None = Header(None, description="Client session identifier"),
    db: AsyncSession = Depends(get_db),
):
    """Return aggregate portfolio statistics for the session."""
    token = _token(x_session_token)
    service = PortfolioService(db)
    return await service.get_summary(token)


# ── POST /portfolio ────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Add a property to portfolio",
    description=(
        "Add a property to the investor's tracked portfolio. Optionally include "
        "purchase price, down payment %, mortgage rate, loan term, actual monthly "
        "rent, and status. Returns the full entry with computed financial metrics "
        "(equity, monthly mortgage, cash flow, cash-on-cash return)."
    ),
)
async def add_to_portfolio(
    payload: PortfolioEntryCreate,
    x_session_token: str | None = Header(None, description="Client session identifier"),
    db: AsyncSession = Depends(get_db),
):
    """Add a property to the portfolio with financial parameters."""
    token = _token(x_session_token)
    service = PortfolioService(db)
    try:
        entry = await service.add_entry(token, payload)
    except ValueError as e:
        detail = str(e)
        if "already in your portfolio" in detail:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    # Re-fetch as enriched response
    entries = await service.list_entries(token)
    enriched = next((e for e in entries if e["id"] == entry.id), None)
    return enriched or {"id": entry.id, "message": "Portfolio entry created."}


# ── GET /portfolio ─────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=List[Dict[str, Any]],
    summary="List portfolio entries",
    description=(
        "Returns all portfolio entries for the session with full property detail "
        "and computed financial metrics (equity, monthly mortgage, cash flow, "
        "cash-on-cash return). Optionally filter by status."
    ),
)
async def list_portfolio(
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status: active | sold | under_contract | watchlist",
    ),
    x_session_token: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """List all portfolio entries for the session."""
    token = _token(x_session_token)
    service = PortfolioService(db)
    return await service.list_entries(token, status=status_filter)


# ── PUT /portfolio/{id} ────────────────────────────────────────────────────────

@router.put(
    "/{entry_id}",
    response_model=Dict[str, Any],
    summary="Update a portfolio entry",
    description=(
        "Update one or more fields of a portfolio entry (purchase price, "
        "mortgage details, rent, notes, status). Only fields included in the "
        "request body are updated (PATCH semantics)."
    ),
)
async def update_portfolio_entry(
    entry_id: int,
    payload: PortfolioEntryUpdate,
    x_session_token: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Partially update a portfolio entry."""
    token = _token(x_session_token)
    service = PortfolioService(db)

    updated = await service.update_entry(token, entry_id, payload)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio entry {entry_id} not found for this session.",
        )

    # Return enriched response
    entries = await service.list_entries(token)
    enriched = next((e for e in entries if e["id"] == entry_id), None)
    return enriched or {"id": entry_id, "message": "Portfolio entry updated."}


# ── DELETE /portfolio/{id} ─────────────────────────────────────────────────────

@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a property from portfolio",
    description="Remove a specific entry from the session's portfolio. Irreversible.",
)
async def remove_from_portfolio(
    entry_id: int,
    x_session_token: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Remove a portfolio entry."""
    token = _token(x_session_token)
    service = PortfolioService(db)
    deleted = await service.remove_entry(token, entry_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio entry {entry_id} not found for this session.",
        )
    # 204 No Content — no response body
