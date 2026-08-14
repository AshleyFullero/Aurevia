"""
Tests for /api/v1/properties endpoints.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.property import Property


# ── GET /api/v1/properties ────────────────────────────────────────────────────

async def test_list_properties_empty(client: AsyncClient):
    """Returns empty paginated result when no properties exist."""
    resp = await client.get("/api/v1/properties")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["page"] == 1


async def test_list_properties_with_data(client: AsyncClient, multiple_properties):
    """Returns correct total and first page of properties."""
    resp = await client.get("/api/v1/properties")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == len(multiple_properties)
    assert len(data["items"]) == len(multiple_properties)


async def test_filter_by_city(client: AsyncClient, multiple_properties):
    """Filtering by city returns only matching properties."""
    resp = await client.get("/api/v1/properties", params={"city": "Austin"})
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert "Austin" in item["city"]


async def test_filter_by_state(client: AsyncClient, multiple_properties):
    """Filtering by state returns only matching properties."""
    resp = await client.get("/api/v1/properties", params={"state": "FL"})
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["state"] == "FL"


async def test_filter_by_min_price(client: AsyncClient, multiple_properties):
    """min_price filter excludes properties below the threshold."""
    resp = await client.get("/api/v1/properties", params={"min_price": 600000})
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["list_price"] >= 600000


async def test_filter_by_max_price(client: AsyncClient, multiple_properties):
    """max_price filter excludes properties above the threshold."""
    resp = await client.get("/api/v1/properties", params={"max_price": 500000})
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["list_price"] <= 500000


async def test_filter_by_bedrooms(client: AsyncClient, multiple_properties):
    """Exact bedroom count filter."""
    resp = await client.get("/api/v1/properties", params={"bedrooms": 2})
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["bedrooms"] == 2


async def test_filter_by_min_bedrooms(client: AsyncClient, multiple_properties):
    """min_bedrooms filter."""
    resp = await client.get("/api/v1/properties", params={"min_bedrooms": 3})
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["bedrooms"] >= 3


async def test_filter_by_property_type(client: AsyncClient, multiple_properties):
    """Property type filter."""
    resp = await client.get("/api/v1/properties", params={"property_type": "apartment"})
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["property_type"] == "apartment"


async def test_filter_by_min_cap_rate(client: AsyncClient, multiple_properties):
    """min_cap_rate filter works correctly."""
    resp = await client.get("/api/v1/properties", params={"min_cap_rate": 0.07})
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["metrics"]["cap_rate"] >= 0.07


async def test_filter_by_max_risk_score(client: AsyncClient, multiple_properties):
    """max_risk_score filter excludes high-risk properties."""
    resp = await client.get("/api/v1/properties", params={"max_risk_score": 35})
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["metrics"]["risk_score"] <= 35


async def test_pagination(client: AsyncClient, multiple_properties):
    """Pagination returns correct page slices."""
    resp = await client.get("/api/v1/properties", params={"page": 1, "page_size": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 3  # 6 total / 2 per page


async def test_pagination_second_page(client: AsyncClient, multiple_properties):
    """Second page returns different results."""
    resp1 = await client.get("/api/v1/properties", params={"page": 1, "page_size": 2})
    resp2 = await client.get("/api/v1/properties", params={"page": 2, "page_size": 2})
    ids_p1 = {item["id"] for item in resp1.json()["items"]}
    ids_p2 = {item["id"] for item in resp2.json()["items"]}
    assert ids_p1.isdisjoint(ids_p2)


async def test_sort_by_list_price_asc(client: AsyncClient, multiple_properties):
    """Sorting by list_price asc returns prices in ascending order."""
    resp = await client.get("/api/v1/properties", params={"sort_by": "list_price", "sort_order": "asc"})
    assert resp.status_code == 200
    prices = [item["list_price"] for item in resp.json()["items"]]
    assert prices == sorted(prices)


async def test_sort_by_list_price_desc(client: AsyncClient, multiple_properties):
    """Sorting by list_price desc returns prices in descending order."""
    resp = await client.get("/api/v1/properties", params={"sort_by": "list_price", "sort_order": "desc"})
    assert resp.status_code == 200
    prices = [item["list_price"] for item in resp.json()["items"]]
    assert prices == sorted(prices, reverse=True)


async def test_invalid_sort_by_returns_422(client: AsyncClient):
    """Invalid sort_by field returns 422 Unprocessable Entity."""
    resp = await client.get("/api/v1/properties", params={"sort_by": "invalid_field"})
    assert resp.status_code == 422


# ── GET /api/v1/properties/{id} ───────────────────────────────────────────────

async def test_get_property_by_id(client: AsyncClient, sample_property: Property):
    """Returns correct property data for a known ID."""
    resp = await client.get(f"/api/v1/properties/{sample_property.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == sample_property.id
    assert data["address"] == sample_property.address
    assert data["city"] == sample_property.city
    assert data["list_price"] == sample_property.list_price


async def test_get_property_includes_metrics(client: AsyncClient, sample_property: Property):
    """Property response includes computed investment metrics."""
    resp = await client.get(f"/api/v1/properties/{sample_property.id}")
    assert resp.status_code == 200
    data = resp.json()
    metrics = data["metrics"]
    assert metrics["cap_rate"] == sample_property.cap_rate
    assert metrics["cap_rate_pct"] is not None
    assert metrics["risk_label"] == "Low Risk"  # risk_score=25


async def test_get_property_not_found(client: AsyncClient):
    """Returns 404 for a non-existent property ID."""
    resp = await client.get("/api/v1/properties/99999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


async def test_list_price_formatted(client: AsyncClient, sample_property: Property):
    """list_price_formatted field is human-readable."""
    resp = await client.get(f"/api/v1/properties/{sample_property.id}")
    assert resp.status_code == 200
    formatted = resp.json()["list_price_formatted"]
    assert formatted.startswith("$")
    assert "," in formatted  # e.g. "$900,000"


# ── POST /api/v1/properties/match ─────────────────────────────────────────────

async def test_match_returns_scored_properties(client: AsyncClient, multiple_properties):
    """Match endpoint returns scored properties sorted by match_score desc."""
    payload = {
        "preferred_cities": ["Austin"],
        "preferred_states": ["TX"],
        "max_budget": 1_000_000,
        "target_cap_rate": 0.07,
        "max_risk_score": 50,
        "limit": 5,
    }
    resp = await client.post("/api/v1/properties/match", json=payload)
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    # All items should have a match_score
    for item in items:
        assert item["match_score"] is not None
        assert 0 <= item["match_score"] <= 100
        assert item["match_label"] is not None


async def test_match_sorted_by_score_desc(client: AsyncClient, multiple_properties):
    """Match results are sorted by match_score in descending order."""
    payload = {
        "preferred_cities": ["Austin", "Miami"],
        "max_budget": 2_000_000,
        "limit": 10,
    }
    resp = await client.post("/api/v1/properties/match", json=payload)
    assert resp.status_code == 200
    items = resp.json()
    scores = [item["match_score"] for item in items]
    assert scores == sorted(scores, reverse=True)


async def test_match_respects_limit(client: AsyncClient, multiple_properties):
    """Match endpoint respects the limit parameter."""
    payload = {"limit": 2}
    resp = await client.post("/api/v1/properties/match", json=payload)
    assert resp.status_code == 200
    assert len(resp.json()) <= 2


async def test_match_empty_db(client: AsyncClient):
    """Match with no properties returns empty list."""
    payload = {"limit": 5}
    resp = await client.post("/api/v1/properties/match", json=payload)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_match_budget_filter_applied(client: AsyncClient, multiple_properties):
    """Match hard-filters by max_budget before scoring."""
    payload = {
        "max_budget": 400_100,  # Only the cheapest should pass
        "limit": 10,
    }
    resp = await client.post("/api/v1/properties/match", json=payload)
    assert resp.status_code == 200
    # All results must be at or under budget (with slack tolerance)
    for item in resp.json():
        assert item["list_price"] <= 400_100
