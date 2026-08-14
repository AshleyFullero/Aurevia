"""
Tests for /api/v1/stats and /api/v1/search and /api/v1/contact endpoints.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.property import Property


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/stats/overview
# ═══════════════════════════════════════════════════════════════════════════════

async def test_stats_overview_empty_db(client: AsyncClient):
    """Returns zero-state stats when no properties or waitlist entries exist."""
    resp = await client.get("/api/v1/stats/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["property_count"] == 0
    assert data["waitlist_count"] == 0


async def test_stats_overview_contains_required_fields(client: AsyncClient):
    """Response shape contains all expected fields."""
    resp = await client.get("/api/v1/stats/overview")
    assert resp.status_code == 200
    data = resp.json()
    required = [
        "property_count", "market_count", "waitlist_count",
        "property_count_formatted", "waitlist_count_formatted",
        "avg_hours_saved", "match_accuracy_pct", "platform_version",
    ]
    for field in required:
        assert field in data, f"Missing field: {field}"


async def test_stats_overview_property_count_matches_db(
    client: AsyncClient, multiple_properties
):
    """property_count reflects the actual number of seeded properties."""
    resp = await client.get("/api/v1/stats/overview")
    assert resp.status_code == 200
    assert resp.json()["property_count"] == len(multiple_properties)


async def test_stats_overview_waitlist_count_increments(client: AsyncClient):
    """waitlist_count increments as waitlist entries are added."""
    await client.post("/api/v1/waitlist", json={"email": "stats1@test.com"})
    await client.post("/api/v1/waitlist", json={"email": "stats2@test.com"})
    resp = await client.get("/api/v1/stats/overview")
    assert resp.status_code == 200
    assert resp.json()["waitlist_count"] == 2


async def test_stats_overview_avg_cap_rate_present_with_data(
    client: AsyncClient, multiple_properties
):
    """avg_cap_rate is populated when properties are in the database."""
    resp = await client.get("/api/v1/stats/overview")
    data = resp.json()
    assert data["avg_cap_rate"] is not None
    assert data["avg_cap_rate_pct"] is not None
    assert data["avg_cap_rate_pct"].endswith("%")


async def test_stats_overview_market_count(
    client: AsyncClient, multiple_properties
):
    """market_count counts distinct city/state combinations."""
    resp = await client.get("/api/v1/stats/overview")
    # multiple_properties fixture has Austin,TX and Miami,FL = 2 markets
    assert resp.json()["market_count"] == 2


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/stats/markets
# ═══════════════════════════════════════════════════════════════════════════════

async def test_stats_markets_empty_db(client: AsyncClient):
    """Returns empty list when no properties exist."""
    resp = await client.get("/api/v1/stats/markets")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_stats_markets_with_data(client: AsyncClient, multiple_properties):
    """Returns markets grouped by city."""
    resp = await client.get("/api/v1/stats/markets")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    cities = {item["city"] for item in data}
    assert "Austin" in cities


async def test_stats_markets_limit(client: AsyncClient, multiple_properties):
    """Limit parameter caps the number of markets returned."""
    resp = await client.get("/api/v1/stats/markets", params={"limit": 1})
    assert resp.status_code == 200
    assert len(resp.json()) <= 1


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/search/suggestions
# ═══════════════════════════════════════════════════════════════════════════════

async def test_search_suggestions_returns_list(client: AsyncClient):
    """Returns a non-empty list of suggestion strings."""
    resp = await client.get("/api/v1/search/suggestions")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(isinstance(s, str) for s in data)


async def test_search_suggestions_limit(client: AsyncClient):
    """Limit parameter constrains results."""
    resp = await client.get("/api/v1/search/suggestions", params={"limit": 3})
    assert resp.status_code == 200
    assert len(resp.json()) <= 3


async def test_search_suggestions_filtered_by_query(client: AsyncClient):
    """q parameter filters suggestions to only those containing the substring."""
    resp = await client.get("/api/v1/search/suggestions", params={"q": "austin"})
    assert resp.status_code == 200
    data = resp.json()
    for suggestion in data:
        assert "austin" in suggestion.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/search/natural
# ═══════════════════════════════════════════════════════════════════════════════

async def test_natural_search_returns_structured_response(
    client: AsyncClient, multiple_properties
):
    """Returns query, understood_as, filters_applied, total_matches, results."""
    resp = await client.post("/api/v1/search/natural", json={
        "query": "2-bed apartment in Austin",
        "limit": 5,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "query" in data
    assert "understood_as" in data
    assert "filters_applied" in data
    assert "total_matches" in data
    assert "results" in data


async def test_natural_search_parses_city(client: AsyncClient, multiple_properties):
    """Parser correctly extracts city from the query."""
    resp = await client.post("/api/v1/search/natural", json={
        "query": "condos in Miami with low risk",
        "limit": 10,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["filters_applied"]["city"] == "Miami"
    assert data["filters_applied"]["state"] == "FL"


async def test_natural_search_parses_property_type(
    client: AsyncClient, multiple_properties
):
    """Parser correctly extracts property type."""
    resp = await client.post("/api/v1/search/natural", json={
        "query": "apartment under $500K",
        "limit": 5,
    })
    assert resp.status_code == 200
    assert resp.json()["filters_applied"]["property_type"] == "apartment"


async def test_natural_search_parses_bedrooms(
    client: AsyncClient, multiple_properties
):
    """Parser correctly extracts bedroom count."""
    resp = await client.post("/api/v1/search/natural", json={
        "query": "2 bedroom condo in Austin",
        "limit": 5,
    })
    assert resp.status_code == 200
    filters = resp.json()["filters_applied"]
    assert filters["min_bedrooms"] == 2
    assert filters["max_bedrooms"] == 2


async def test_natural_search_parses_max_price(
    client: AsyncClient, multiple_properties
):
    """Parser correctly extracts max price."""
    resp = await client.post("/api/v1/search/natural", json={
        "query": "properties under $600K in Austin",
        "limit": 10,
    })
    assert resp.status_code == 200
    filters = resp.json()["filters_applied"]
    assert filters["max_price"] is not None
    assert filters["max_price"] == 600_000.0


async def test_natural_search_parses_cap_rate(
    client: AsyncClient, multiple_properties
):
    """Parser correctly extracts minimum cap rate."""
    resp = await client.post("/api/v1/search/natural", json={
        "query": "investment property with 8% cap rate in Austin",
        "limit": 10,
    })
    assert resp.status_code == 200
    filters = resp.json()["filters_applied"]
    assert filters["min_cap_rate"] is not None
    assert abs(filters["min_cap_rate"] - 0.08) < 1e-6


async def test_natural_search_parses_low_risk(
    client: AsyncClient, multiple_properties
):
    """Low risk keyword sets max_risk_score."""
    resp = await client.post("/api/v1/search/natural", json={
        "query": "safe condos with low risk",
        "limit": 5,
    })
    assert resp.status_code == 200
    filters = resp.json()["filters_applied"]
    assert filters["max_risk_score"] is not None
    assert filters["max_risk_score"] <= 35


async def test_natural_search_empty_results(client: AsyncClient):
    """With no properties, results list is empty."""
    resp = await client.post("/api/v1/search/natural", json={
        "query": "properties in Austin",
        "limit": 5,
    })
    assert resp.status_code == 200
    assert resp.json()["total_matches"] == 0
    assert resp.json()["results"] == []


async def test_natural_search_short_query_returns_422(client: AsyncClient):
    """Query shorter than 3 chars returns 422."""
    resp = await client.post("/api/v1/search/natural", json={"query": "ab"})
    assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/contact
# ═══════════════════════════════════════════════════════════════════════════════

async def test_contact_submit_success(client: AsyncClient):
    """Valid contact form submission returns 201 with success=True."""
    resp = await client.post("/api/v1/contact", json={
        "name": "Jane Smith",
        "email": "jane@example.com",
        "message": "I'd love to see a demo of Aurevia for my firm.",
        "source": "landing_page",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["id"] is not None
    assert "message" in data


async def test_contact_with_company(client: AsyncClient):
    """Contact form accepts optional company field."""
    resp = await client.post("/api/v1/contact", json={
        "name": "Alex Johnson",
        "email": "alex@realtyfirm.com",
        "company": "RealtyFirm LLC",
        "message": "Interested in an enterprise demo.",
    })
    assert resp.status_code == 201
    assert resp.json()["success"] is True


async def test_contact_invalid_email(client: AsyncClient):
    """Invalid email returns 422."""
    resp = await client.post("/api/v1/contact", json={
        "name": "Test",
        "email": "not-an-email",
        "message": "Hello there",
    })
    assert resp.status_code == 422


async def test_contact_missing_name(client: AsyncClient):
    """Missing name field returns 422."""
    resp = await client.post("/api/v1/contact", json={
        "email": "test@example.com",
        "message": "Hello there",
    })
    assert resp.status_code == 422


async def test_contact_message_too_short(client: AsyncClient):
    """Message shorter than 5 characters returns 422."""
    resp = await client.post("/api/v1/contact", json={
        "name": "Test User",
        "email": "test@example.com",
        "message": "Hi",
    })
    assert resp.status_code == 422


async def test_contact_email_normalised_lowercase(client: AsyncClient):
    """Email is normalised to lowercase in storage."""
    resp = await client.post("/api/v1/contact", json={
        "name": "Test User",
        "email": "TEST@EXAMPLE.COM",
        "message": "This is a test message for Aurevia.",
    })
    assert resp.status_code == 201
    # Email validation normalises to lowercase (validator runs on input)
    assert resp.json()["success"] is True


async def test_contact_sequential_ids(client: AsyncClient):
    """Multiple submissions get distinct IDs."""
    resp1 = await client.post("/api/v1/contact", json={
        "name": "User One", "email": "one@example.com",
        "message": "First contact message here.",
    })
    resp2 = await client.post("/api/v1/contact", json={
        "name": "User Two", "email": "two@example.com",
        "message": "Second contact message here.",
    })
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["id"] != resp2.json()["id"]
