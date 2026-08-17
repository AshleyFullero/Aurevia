"""
Compare Router
──────────────
Endpoint:
  GET /api/v1/compare?ids=1,2,3,4  — Side-by-side investment comparison of 2–4 properties

Returns full property data for each, plus a "winner" verdict for each
investment metric category so clients can render comparison tables easily.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.property import Property
from app.schemas.property import PropertyResponse

router = APIRouter(prefix="/compare", tags=["Compare"])


# ── Schema ────────────────────────────────────────────────────────────────────

class MetricWinner(BaseModel):
    """Declares which property wins for a given metric."""
    metric: str
    label: str                     # Human-readable metric name
    winner_id: Optional[int]       # Property ID of the winner (None if tied/no data)
    winner_address: Optional[str]
    values: Dict[int, Optional[str]]   # property_id → formatted value


class CompareResponse(BaseModel):
    """Full side-by-side comparison response."""
    property_ids: List[int]
    properties: List[PropertyResponse]
    winners: List[MetricWinner]
    summary: str                   # e.g., "Property 3 leads in 4 of 6 categories"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _winner(
    properties: List[Property],
    attr: str,
    higher_is_better: bool = True,
) -> tuple[Optional[int], Optional[str]]:
    """Return (property_id, address) of the property with the best value for attr."""
    candidates = [(p, getattr(p, attr)) for p in properties if getattr(p, attr) is not None]
    if not candidates:
        return None, None
    best = max(candidates, key=lambda x: x[1]) if higher_is_better else min(candidates, key=lambda x: x[1])
    prop, _ = best
    # Check for tie
    best_val = getattr(best[0], attr)
    tied = [p for p, v in candidates if v == best_val]
    if len(tied) > 1:
        return None, None  # Tie — no single winner
    return prop.id, prop.address


def _fmt_pct(v: Optional[float]) -> Optional[str]:
    return f"{v * 100:.1f}%" if v is not None else None


def _fmt_price(v: Optional[float]) -> Optional[str]:
    return f"${v:,.0f}" if v is not None else None


def _fmt_int(v: Optional[int]) -> Optional[str]:
    return str(v) if v is not None else None


# ── GET /compare ───────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=CompareResponse,
    summary="Compare 2–4 properties side by side",
    description=(
        "Pass a comma-separated list of 2–4 property IDs (e.g. ?ids=1,3,7). "
        "Returns full property data for each and a 'winners' breakdown — which "
        "property leads in cap rate, rental yield, price, risk, YoY growth, and "
        "vacancy rate. Ideal for rendering a comparison table UI."
    ),
)
async def compare_properties(
    ids: str = Query(
        ...,
        description="Comma-separated property IDs (2–4), e.g. '1,3,7'",
        examples={"default": {"value": "1,2,3"}},
    ),
    db: AsyncSession = Depends(get_db),
):
    """Return a side-by-side investment comparison for 2–4 properties."""

    # Parse & validate IDs
    try:
        id_list = [int(x.strip()) for x in ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ids must be a comma-separated list of integers, e.g. '1,2,3'",
        )

    if len(id_list) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least 2 property IDs to compare.",
        )
    if len(id_list) > 4:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="You can compare at most 4 properties at a time.",
        )
    if len(id_list) != len(set(id_list)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Duplicate property IDs are not allowed.",
        )

    # Fetch properties preserving input order
    result = await db.execute(select(Property).where(Property.id.in_(id_list)))
    raw_props = {p.id: p for p in result.scalars().all()}

    missing = [pid for pid in id_list if pid not in raw_props]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Properties not found: {missing}",
        )

    properties = [raw_props[pid] for pid in id_list]  # preserve requested order
    responses = [PropertyResponse.from_orm_with_metrics(p) for p in properties]

    # ── Build Winners ────────────────────────────────────────────────────────
    METRICS: List[tuple[str, str, bool, Any]] = [
        # (orm_attr, human_label, higher_is_better, formatter)
        ("cap_rate",      "Cap Rate",           True,  _fmt_pct),
        ("rental_yield",  "Rental Yield",        True,  _fmt_pct),
        ("yoy_growth",    "YoY Growth",          True,  _fmt_pct),
        ("risk_score",    "Risk Score",          False, _fmt_int),   # lower = safer
        ("list_price",    "Asking Price",         False, _fmt_price), # lower = better value
        ("vacancy_rate",  "Vacancy Rate",         False, _fmt_pct),
    ]

    winners: List[MetricWinner] = []
    win_counts: Dict[int, int] = {pid: 0 for pid in id_list}

    for attr, label, higher_is_better, formatter in METRICS:
        winner_id, winner_addr = _winner(properties, attr, higher_is_better)
        values = {p.id: formatter(getattr(p, attr)) for p in properties}
        winners.append(MetricWinner(
            metric=attr,
            label=label,
            winner_id=winner_id,
            winner_address=winner_addr,
            values=values,
        ))
        if winner_id is not None:
            win_counts[winner_id] = win_counts.get(winner_id, 0) + 1

    # Build summary sentence
    top_winner_id = max(win_counts, key=win_counts.get)  # type: ignore[arg-type]
    top_wins = win_counts[top_winner_id]
    total_decidable = sum(1 for w in winners if w.winner_id is not None)
    if total_decidable == 0:
        summary = "All metrics tied — properties are very similar."
    else:
        top_prop = raw_props[top_winner_id]
        summary = (
            f"{top_prop.address} leads in {top_wins} of "
            f"{total_decidable} comparable metric{'s' if total_decidable != 1 else ''}."
        )

    return CompareResponse(
        property_ids=id_list,
        properties=responses,
        winners=winners,
        summary=summary,
    )
