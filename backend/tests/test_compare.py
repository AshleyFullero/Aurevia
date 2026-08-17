"""
Tests for GET /api/v1/compare endpoint.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.property import Property


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/compare
# ═══════════════════════════════════════════════════════════════════════════════

async def test_compare_two_properties(client: AsyncClient, multiple_properties: list):
    """Comparing 2 properties returns the full structured response."""
    p1, p2 = multiple_properties[0], multiple_properties[1]
    resp = await client.get(f"/api/v1/compare?ids={p1.id},{p2.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "property_ids" in data
    assert "properties" in data
    assert "winners" in data
    assert "summary" in data
    assert len(data["properties"]) == 2
    assert set(data["property_ids"]) == {p1.id, p2.id}


async def test_compare_four_properties(client: AsyncClient, multiple_properties: list):
    """Comparing 4 properties is the maximum allowed."""
    ids = ",".join(str(p.id) for p in multiple_properties[:4])
    resp = await client.get(f"/api/v1/compare?ids={ids}")
    assert resp.status_code == 200
    assert len(resp.json()["properties"]) == 4


async def test_compare_one_property_returns_422(
    client: AsyncClient, sample_property: Property
):
    """Passing only one ID returns 422 Unprocessable Entity."""
    resp = await client.get(f"/api/v1/compare?ids={sample_property.id}")
    assert resp.status_code == 422


async def test_compare_five_properties_returns_422(
    client: AsyncClient, multiple_properties: list
):
    """Passing 5 IDs returns 422 (exceeds max of 4)."""
    ids = ",".join(str(p.id) for p in multiple_properties[:5])
    resp = await client.get(f"/api/v1/compare?ids={ids}")
    assert resp.status_code == 422


async def test_compare_nonexistent_id_returns_404(
    client: AsyncClient, sample_property: Property
):
    """Passing a nonexistent ID returns 404."""
    resp = await client.get(f"/api/v1/compare?ids={sample_property.id},99999")
    assert resp.status_code == 404


async def test_compare_duplicate_ids_returns_422(
    client: AsyncClient, sample_property: Property
):
    """Duplicate IDs are rejected with 422."""
    resp = await client.get(
        f"/api/v1/compare?ids={sample_property.id},{sample_property.id}"
    )
    assert resp.status_code == 422


async def test_compare_invalid_ids_returns_422(client: AsyncClient):
    """Non-integer IDs return 422."""
    resp = await client.get("/api/v1/compare?ids=abc,def")
    assert resp.status_code == 422


async def test_compare_winners_structure(client: AsyncClient, multiple_properties: list):
    """Winners list contains expected metric categories."""
    p1, p2 = multiple_properties[0], multiple_properties[1]
    resp = await client.get(f"/api/v1/compare?ids={p1.id},{p2.id}")
    assert resp.status_code == 200
    winners = resp.json()["winners"]
    metric_names = {w["metric"] for w in winners}
    assert "cap_rate" in metric_names
    assert "rental_yield" in metric_names
    assert "risk_score" in metric_names
    assert "list_price" in metric_names


async def test_compare_summary_is_string(client: AsyncClient, multiple_properties: list):
    """Summary is a non-empty string."""
    p1, p2 = multiple_properties[0], multiple_properties[1]
    resp = await client.get(f"/api/v1/compare?ids={p1.id},{p2.id}")
    assert resp.status_code == 200
    summary = resp.json()["summary"]
    assert isinstance(summary, str)
    assert len(summary) > 0


async def test_compare_preserves_order(client: AsyncClient, multiple_properties: list):
    """Properties in the response are returned in the same order as the input IDs."""
    p1, p2, p3 = multiple_properties[0], multiple_properties[1], multiple_properties[2]
    resp = await client.get(f"/api/v1/compare?ids={p3.id},{p1.id},{p2.id}")
    assert resp.status_code == 200
    returned_ids = [p["id"] for p in resp.json()["properties"]]
    assert returned_ids == [p3.id, p1.id, p2.id]
