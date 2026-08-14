"""
Search Router
─────────────
Endpoints:
  GET  /api/v1/search/suggestions    — AI query auto-complete suggestions
  POST /api/v1/search/natural        — Parse a natural-language property query
                                       into structured search parameters
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.property import Property
from app.schemas.common import PaginatedResponse
from app.schemas.property import PropertyResponse
from app.services.property_service import PropertyService, PropertySearchParams

router = APIRouter(prefix="/search", tags=["Search"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class NaturalLanguageQuery(BaseModel):
    """A free-text investor query to be parsed into structured filters."""
    query: str = Field(..., min_length=3, max_length=500, description="Natural language query")
    limit: int = Field(10, ge=1, le=50, description="Max results to return")


class ParsedQuery(BaseModel):
    """Structured filters extracted from a natural-language query."""
    original_query: str
    city: Optional[str] = None
    state: Optional[str] = None
    property_type: Optional[str] = None
    min_bedrooms: Optional[int] = None
    max_bedrooms: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_cap_rate: Optional[float] = None
    min_yield: Optional[float] = None
    max_risk_score: Optional[int] = None
    sort_by: str = "cap_rate"
    sort_order: str = "desc"
    # Human-readable summary of what was understood
    understood_as: str = ""


# ── Utility: Rule-based NLP parser ────────────────────────────────────────────

_CITIES = {
    "austin": ("Austin", "TX"),
    "miami": ("Miami", "FL"),
    "denver": ("Denver", "CO"),
    "nashville": ("Nashville", "TN"),
    "seattle": ("Seattle", "WA"),
    "phoenix": ("Phoenix", "AZ"),
    "new york": ("New York", "NY"),
    "nyc": ("New York", "NY"),
    "chicago": ("Chicago", "IL"),
    "boston": ("Boston", "MA"),
    "san francisco": ("San Francisco", "CA"),
    "la": ("Los Angeles", "CA"),
    "los angeles": ("Los Angeles", "CA"),
    "dallas": ("Dallas", "TX"),
    "houston": ("Houston", "TX"),
    "charlotte": ("Charlotte", "NC"),
    "raleigh": ("Raleigh", "NC"),
}

_PROPERTY_TYPES = {
    "apartment": "apartment", "studio": "apartment",
    "condo": "condo", "condominium": "condo",
    "townhouse": "townhouse", "townhome": "townhouse",
    "single family": "single_family", "single-family": "single_family",
    "house": "single_family", "home": "single_family", "sfr": "single_family",
    "multi family": "multi_family", "multi-family": "multi_family",
    "duplex": "multi_family", "multifamily": "multi_family",
}


def _parse_query(query: str) -> ParsedQuery:
    """
    Rule-based NLP parser that extracts structured search parameters
    from a free-text investor query.

    Examples:
      "2-bed investment property with 8%+ cap rate in Austin TX"
        → city=Austin, state=TX, min_bedrooms=2, min_cap_rate=0.08

      "luxury condo under $1M in Miami with low risk"
        → property_type=condo, city=Miami, max_price=1_000_000, max_risk_score=30
    """
    q = query.lower()
    parsed = ParsedQuery(original_query=query)
    clues: list[str] = []

    # ── Location ────────────────────────────────────────────────────────────
    for keyword, (city, state) in _CITIES.items():
        if keyword in q:
            parsed.city = city
            parsed.state = state
            clues.append(f"city: {city}, {state}")
            break

    # ── Property Type ────────────────────────────────────────────────────────
    for keyword, ptype in _PROPERTY_TYPES.items():
        if keyword in q:
            parsed.property_type = ptype
            clues.append(f"type: {ptype}")
            break

    # ── Bedrooms ─────────────────────────────────────────────────────────────
    bed_match = re.search(r'(\d+)\s*(?:-|\s*to\s*)?(\d+)?\s*(?:bed|br|bedroom)', q)
    if bed_match:
        lo = int(bed_match.group(1))
        hi = int(bed_match.group(2)) if bed_match.group(2) else None
        parsed.min_bedrooms = lo
        if hi:
            parsed.max_bedrooms = hi
            clues.append(f"bedrooms: {lo}–{hi}")
        else:
            parsed.max_bedrooms = lo
            clues.append(f"bedrooms: {lo}")

    # ── Price ─────────────────────────────────────────────────────────────────
    price_match = re.search(
        r'(?:under|below|max|less than|<)\s*\$?([\d,.]+)\s*(k|m|million|thousand)?', q
    )
    if price_match:
        amount = float(price_match.group(1).replace(",", ""))
        suffix = (price_match.group(2) or "").lower()
        if suffix in ("m", "million"):
            amount *= 1_000_000
        elif suffix in ("k", "thousand"):
            amount *= 1_000
        parsed.max_price = amount
        clues.append(f"max price: ${amount:,.0f}")

    price_min_match = re.search(
        r'(?:above|over|min|more than|>|from)\s*\$?([\d,.]+)\s*(k|m|million|thousand)?', q
    )
    if price_min_match:
        amount = float(price_min_match.group(1).replace(",", ""))
        suffix = (price_min_match.group(2) or "").lower()
        if suffix in ("m", "million"):
            amount *= 1_000_000
        elif suffix in ("k", "thousand"):
            amount *= 1_000
        parsed.min_price = amount
        clues.append(f"min price: ${amount:,.0f}")

    # ── Cap Rate ──────────────────────────────────────────────────────────────
    cap_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*\+?\s*(?:cap rate|cap)', q)
    if cap_match:
        pct = float(cap_match.group(1)) / 100
        parsed.min_cap_rate = pct
        clues.append(f"min cap rate: {float(cap_match.group(1))}%")

    # ── Yield ─────────────────────────────────────────────────────────────────
    yield_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*\+?\s*(?:yield|rental yield|gross yield)', q)
    if yield_match:
        pct = float(yield_match.group(1)) / 100
        parsed.min_yield = pct
        clues.append(f"min yield: {float(yield_match.group(1))}%")

    # ── Risk ──────────────────────────────────────────────────────────────────
    if any(w in q for w in ["low risk", "safe", "low-risk", "conservative"]):
        parsed.max_risk_score = 35
        clues.append("risk: low")
    elif any(w in q for w in ["medium risk", "moderate"]):
        parsed.max_risk_score = 65
        clues.append("risk: medium")

    # ── Sort hints ────────────────────────────────────────────────────────────
    if "appreciation" in q or "growth" in q:
        parsed.sort_by = "cap_rate"
    elif "cheap" in q or "affordable" in q or "lowest price" in q:
        parsed.sort_by = "list_price"
        parsed.sort_order = "asc"
    elif "expensive" in q or "luxury" in q or "premium" in q:
        parsed.sort_by = "list_price"
        parsed.sort_order = "desc"
    elif "new" in q or "recently listed" in q:
        parsed.sort_by = "created_at"
        parsed.sort_order = "desc"

    parsed.understood_as = "; ".join(clues) if clues else "general search (no specific filters detected)"
    return parsed


# ── GET /search/suggestions ───────────────────────────────────────────────────

# Pre-baked AI-style query suggestions for the autocomplete widget
_SUGGESTIONS = [
    "Find me a 2-bed investment property with 8%+ cap rate in Austin, TX",
    "Show condos under $800K in Miami with low risk",
    "Multi-family properties with 9%+ yield in Nashville",
    "Luxury apartments in Denver under $1M",
    "Single-family homes in Phoenix with high appreciation potential",
    "2–3 bedroom apartments with 7%+ yield in Seattle",
    "Townhouses in Austin under $700K with low vacancy",
    "Investment properties in Miami with cap rate above 9%",
    "What are the best markets for cap rate right now?",
    "Show me properties with risk score below 30",
    "Affordable condos in Denver with strong YoY growth",
    "High-yield properties across all markets, sorted by return",
]


@router.get(
    "/suggestions",
    response_model=List[str],
    summary="AI query auto-complete suggestions",
    description=(
        "Returns a curated list of AI-style natural-language query suggestions "
        "for the dashboard search bar autocomplete. Optionally filters by a partial "
        "query string."
    ),
)
async def get_suggestions(
    q: Optional[str] = Query(None, description="Partial query to filter suggestions by"),
    limit: int = Query(5, ge=1, le=12),
):
    """Return query autocomplete suggestions, optionally filtered by prefix."""
    suggestions = _SUGGESTIONS
    if q:
        q_lower = q.lower()
        suggestions = [s for s in suggestions if q_lower in s.lower()]
    return suggestions[:limit]


# ── POST /search/natural ──────────────────────────────────────────────────────

@router.post(
    "/natural",
    response_model=Dict[str, Any],
    summary="Parse natural-language property query",
    description=(
        "Accepts a free-text investor query (e.g. '2-bed condo under $1M in Austin "
        "with 8%+ cap rate') and returns both the parsed structured filters and "
        "the matching properties from the database."
    ),
)
async def natural_language_search(
    payload: NaturalLanguageQuery,
    db: AsyncSession = Depends(get_db),
):
    """Parse a natural-language query and return matching properties."""
    parsed = _parse_query(payload.query)

    # Build search params from parsed fields
    import math
    params = PropertySearchParams(
        city=parsed.city,
        state=parsed.state,
        property_type=parsed.property_type,
        min_bedrooms=parsed.min_bedrooms,
        max_bedrooms=parsed.max_bedrooms,
        min_price=parsed.min_price,
        max_price=parsed.max_price,
        min_cap_rate=parsed.min_cap_rate,
        min_yield=parsed.min_yield,
        max_risk_score=parsed.max_risk_score,
        sort_by=parsed.sort_by,
        sort_order=parsed.sort_order,
        page=1,
        page_size=payload.limit,
    )

    service = PropertyService(db)
    items, total = await service.search(params)

    return {
        "query": payload.query,
        "understood_as": parsed.understood_as,
        "filters_applied": {
            "city": parsed.city,
            "state": parsed.state,
            "property_type": parsed.property_type,
            "min_bedrooms": parsed.min_bedrooms,
            "max_bedrooms": parsed.max_bedrooms,
            "min_price": parsed.min_price,
            "max_price": parsed.max_price,
            "min_cap_rate": parsed.min_cap_rate,
            "min_yield": parsed.min_yield,
            "max_risk_score": parsed.max_risk_score,
        },
        "total_matches": total,
        "results": items,
    }
