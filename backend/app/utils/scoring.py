"""
Aurevia Match Scoring Engine
────────────────────────────
A rule-based multi-criteria scoring algorithm that ranks properties
against an investor's profile (budget, location, investment goals, risk).

Each criterion contributes a weighted component score (0–100).
The final match score is the weighted average, clamped to 0–100.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.property import Property
    from app.schemas.property import MatchRequest


# ── Weights (must sum to 1.0) ─────────────────────────────────────────────────
WEIGHTS = {
    "location":   0.25,   # City/state preference match
    "budget":     0.20,   # Within budget range
    "cap_rate":   0.20,   # Meets cap rate target
    "yield":      0.15,   # Meets rental yield target
    "risk":       0.10,   # Risk score within tolerance
    "type":       0.05,   # Property type preference
    "bedrooms":   0.05,   # Bedroom count preference
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"


def compute_match_score(prop: "Property", profile: "MatchRequest") -> int:
    """
    Compute a 0–100 match score for a property against an investor profile.

    Returns an integer score where:
      90–100 = Excellent Match
      75–89  = Good Match
      60–74  = Fair Match
      < 60   = Poor Match
    """
    scores: dict[str, float] = {}

    # ── Location ──────────────────────────────────────────────────────────────
    loc_score = 0.0
    if profile.preferred_cities:
        city_match = any(
            c.lower() in prop.city.lower() for c in profile.preferred_cities
        )
        loc_score += 60 if city_match else 0
    else:
        loc_score += 60  # No preference = full score

    if profile.preferred_states:
        state_match = any(
            s.upper() == prop.state.upper() for s in profile.preferred_states
        )
        loc_score += 40 if state_match else 0
    else:
        loc_score += 40  # No preference = full score

    scores["location"] = min(loc_score, 100)

    # ── Budget ────────────────────────────────────────────────────────────────
    budget_score = 100.0
    if profile.max_budget and prop.list_price > profile.max_budget:
        # Penalise proportionally based on how far over budget
        over_pct = (prop.list_price - profile.max_budget) / profile.max_budget
        budget_score = max(0.0, 100.0 - over_pct * 200)
    if profile.min_budget and prop.list_price < profile.min_budget:
        under_pct = (profile.min_budget - prop.list_price) / profile.min_budget
        budget_score = max(0.0, budget_score - under_pct * 100)
    scores["budget"] = budget_score

    # ── Cap Rate ──────────────────────────────────────────────────────────────
    if profile.target_cap_rate and prop.cap_rate is not None:
        diff = prop.cap_rate - profile.target_cap_rate
        # Reward properties that meet or exceed target cap rate
        if diff >= 0:
            cap_score = min(100.0, 80 + diff * 500)
        else:
            cap_score = max(0.0, 80 + diff * 800)  # Penalise shortfall more
        scores["cap_rate"] = cap_score
    else:
        scores["cap_rate"] = 70  # Neutral when no target set

    # ── Rental Yield ──────────────────────────────────────────────────────────
    if profile.target_yield and prop.rental_yield is not None:
        diff = prop.rental_yield - profile.target_yield
        if diff >= 0:
            yield_score = min(100.0, 80 + diff * 500)
        else:
            yield_score = max(0.0, 80 + diff * 800)
        scores["yield"] = yield_score
    else:
        scores["yield"] = 70

    # ── Risk ──────────────────────────────────────────────────────────────────
    if profile.max_risk_score is not None and prop.risk_score is not None:
        if prop.risk_score <= profile.max_risk_score:
            # How much margin below the tolerance? Reward safer properties.
            margin = profile.max_risk_score - prop.risk_score
            risk_score = min(100.0, 70 + margin * 1.5)
        else:
            over = prop.risk_score - profile.max_risk_score
            risk_score = max(0.0, 70 - over * 3)
        scores["risk"] = risk_score
    else:
        scores["risk"] = 70

    # ── Property Type ─────────────────────────────────────────────────────────
    if profile.preferred_property_types:
        type_match = prop.property_type.lower() in [
            t.lower() for t in profile.preferred_property_types
        ]
        scores["type"] = 100 if type_match else 30
    else:
        scores["type"] = 100

    # ── Bedrooms ──────────────────────────────────────────────────────────────
    bed_score = 100.0
    if profile.min_bedrooms and prop.bedrooms < profile.min_bedrooms:
        bed_score = max(0.0, 100 - (profile.min_bedrooms - prop.bedrooms) * 30)
    if profile.max_bedrooms and prop.bedrooms > profile.max_bedrooms:
        bed_score = max(0.0, bed_score - (prop.bedrooms - profile.max_bedrooms) * 30)
    scores["bedrooms"] = bed_score

    # ── Weighted Final Score ───────────────────────────────────────────────────
    final = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)
    return int(round(max(0, min(100, final))))


def match_label(score: int) -> str:
    """Convert a numeric match score to a human-readable label."""
    if score >= 90:
        return "Excellent Match"
    if score >= 75:
        return "Good Match"
    if score >= 60:
        return "Fair Match"
    return "Poor Match"


def risk_label(score: Optional[int]) -> Optional[str]:
    """Convert a numeric risk score to a label."""
    if score is None:
        return None
    if score <= 30:
        return "Low Risk"
    if score <= 65:
        return "Medium Risk"
    return "High Risk"


def format_pct(value: Optional[float]) -> Optional[str]:
    """Format a decimal fraction as a percentage string (e.g., 0.084 → '8.4%')."""
    if value is None:
        return None
    return f"{value * 100:.1f}%"
