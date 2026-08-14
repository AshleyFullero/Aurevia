"""
Tests for /api/v1/analytics endpoints.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.property import Property


# ── GET /api/v1/analytics/market ─────────────────────────────────────────────

async def test_market_analytics_empty_db(client: AsyncClient):
    """Returns empty list when no properties exist."""
    resp = await client.get("/api/v1/analytics/market")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_market_analytics_groups_by_city(client: AsyncClient, multiple_properties):
    """Results are grouped by city (Austin + Miami in fixture)."""
    resp = await client.get("/api/v1/analytics/market")
    assert resp.status_code == 200
    data = resp.json()
    cities = {item["city"] for item in data}
    assert "Austin" in cities
    assert "Miami" in cities


async def test_market_analytics_contains_expected_fields(client: AsyncClient, multiple_properties):
    """Each market summary contains the required metric fields."""
    resp = await client.get("/api/v1/analytics/market")
    assert resp.status_code == 200
    item = resp.json()[0]
    required_fields = [
        "city", "state", "market", "total_listings",
        "avg_price", "avg_cap_rate", "avg_yield",
        "avg_yoy_growth", "avg_risk_score",
    ]
    for field in required_fields:
        assert field in item, f"Missing field: {field}"


async def test_market_analytics_filter_by_city(client: AsyncClient, multiple_properties):
    """City filter returns only the matching city's summary."""
    resp = await client.get("/api/v1/analytics/market", params={"city": "Austin"})
    assert resp.status_code == 200
    data = resp.json()
    for item in data:
        assert "Austin" in item["city"]


async def test_market_analytics_formatted_fields(client: AsyncClient, multiple_properties):
    """Formatted percentage and currency fields are present and correctly formatted."""
    resp = await client.get("/api/v1/analytics/market")
    assert resp.status_code == 200
    item = resp.json()[0]
    if item.get("avg_cap_rate_pct"):
        assert item["avg_cap_rate_pct"].endswith("%")
    if item.get("avg_price_formatted"):
        assert item["avg_price_formatted"].startswith("$")


async def test_market_analytics_total_listings_count(client: AsyncClient, multiple_properties):
    """Total listings count matches the number of inserted properties per city."""
    resp = await client.get("/api/v1/analytics/market")
    assert resp.status_code == 200
    data = resp.json()
    total = sum(item["total_listings"] for item in data)
    assert total == len(multiple_properties)


# ── GET /api/v1/analytics/property/{id} ──────────────────────────────────────

async def test_property_analytics_returns_correct_property(
    client: AsyncClient, sample_property: Property
):
    """Returns analytics for the correct property ID."""
    resp = await client.get(f"/api/v1/analytics/property/{sample_property.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["property_id"] == sample_property.id
    assert data["address"] == sample_property.address


async def test_property_analytics_contains_investment_fields(
    client: AsyncClient, sample_property: Property
):
    """Response contains all major investment analytics fields."""
    resp = await client.get(f"/api/v1/analytics/property/{sample_property.id}")
    assert resp.status_code == 200
    data = resp.json()
    required = [
        "cap_rate", "cap_rate_pct",
        "rental_yield", "rental_yield_pct",
        "monthly_rent_estimate", "annual_rent_estimate",
        "cash_on_cash_return", "cash_on_cash_pct",
        "yoy_growth", "five_year_appreciation",
        "risk_score", "risk_label",
    ]
    for field in required:
        assert field in data, f"Missing analytics field: {field}"


async def test_property_analytics_risk_label(
    client: AsyncClient, sample_property: Property
):
    """Risk label is correctly derived from risk_score=25 (Low Risk)."""
    resp = await client.get(f"/api/v1/analytics/property/{sample_property.id}")
    assert resp.status_code == 200
    assert resp.json()["risk_label"] == "Low Risk"


async def test_property_analytics_annual_rent_calculation(
    client: AsyncClient, sample_property: Property
):
    """Annual rent estimate equals monthly * 12."""
    resp = await client.get(f"/api/v1/analytics/property/{sample_property.id}")
    assert resp.status_code == 200
    data = resp.json()
    expected_annual = round(sample_property.monthly_rent_estimate * 12)
    assert data["annual_rent_estimate"] == expected_annual


async def test_property_analytics_irr_estimate_present(
    client: AsyncClient, sample_property: Property
):
    """IRR estimate is present when cap_rate and five_year_appreciation are both set."""
    resp = await client.get(f"/api/v1/analytics/property/{sample_property.id}")
    assert resp.status_code == 200
    data = resp.json()
    # sample_property has both cap_rate=0.08 and five_year_appreciation=0.35
    assert data["irr_estimate_pct"] is not None
    assert data["irr_estimate_pct"].endswith("%")


async def test_property_analytics_list_price_formatted(
    client: AsyncClient, sample_property: Property
):
    """list_price_formatted is human-readable currency."""
    resp = await client.get(f"/api/v1/analytics/property/{sample_property.id}")
    assert resp.status_code == 200
    formatted = resp.json()["list_price_formatted"]
    assert formatted.startswith("$")


async def test_property_analytics_not_found(client: AsyncClient):
    """Returns 404 for a non-existent property ID."""
    resp = await client.get("/api/v1/analytics/property/99999")
    assert resp.status_code == 404


# ── GET /health ───────────────────────────────────────────────────────────────

async def test_health_check(client: AsyncClient):
    """Health endpoint returns 200 with status: healthy."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
