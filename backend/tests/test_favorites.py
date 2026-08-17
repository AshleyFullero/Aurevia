"""
Tests for /api/v1/favorites endpoints.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.property import Property


# ── Helpers ───────────────────────────────────────────────────────────────────

TOKEN = "test-session-abc123"
TOKEN_B = "other-session-xyz789"


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/favorites
# ═══════════════════════════════════════════════════════════════════════════════

async def test_add_favorite_success(client: AsyncClient, sample_property: Property):
    """Adding a valid property returns 201 with success=True."""
    resp = await client.post(
        "/api/v1/favorites",
        json={"property_id": sample_property.id},
        headers={"X-Session-Token": TOKEN},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["property_id"] == sample_property.id
    assert data["session_token"] == TOKEN


async def test_add_favorite_nonexistent_property(client: AsyncClient):
    """Adding a favorite for a property that doesn't exist returns 404."""
    resp = await client.post(
        "/api/v1/favorites",
        json={"property_id": 99999},
        headers={"X-Session-Token": TOKEN},
    )
    assert resp.status_code == 404


async def test_add_duplicate_favorite_returns_409(
    client: AsyncClient, sample_property: Property
):
    """Favoriting the same property twice returns 409 Conflict."""
    payload = {"property_id": sample_property.id}
    headers = {"X-Session-Token": TOKEN}
    await client.post("/api/v1/favorites", json=payload, headers=headers)
    resp = await client.post("/api/v1/favorites", json=payload, headers=headers)
    assert resp.status_code == 409


async def test_add_favorite_without_token_uses_anonymous(
    client: AsyncClient, sample_property: Property
):
    """Requests without X-Session-Token fall back to 'anonymous' session."""
    resp = await client.post(
        "/api/v1/favorites",
        json={"property_id": sample_property.id},
    )
    assert resp.status_code == 201
    assert resp.json()["session_token"] == "anonymous"


async def test_different_sessions_can_favorite_same_property(
    client: AsyncClient, sample_property: Property
):
    """Two different session tokens can favorite the same property."""
    r1 = await client.post(
        "/api/v1/favorites",
        json={"property_id": sample_property.id},
        headers={"X-Session-Token": TOKEN},
    )
    r2 = await client.post(
        "/api/v1/favorites",
        json={"property_id": sample_property.id},
        headers={"X-Session-Token": TOKEN_B},
    )
    assert r1.status_code == 201
    assert r2.status_code == 201


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/favorites
# ═══════════════════════════════════════════════════════════════════════════════

async def test_list_favorites_empty(client: AsyncClient):
    """Empty favorites list returns []."""
    resp = await client.get(
        "/api/v1/favorites",
        headers={"X-Session-Token": TOKEN},
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_favorites_returns_property_data(
    client: AsyncClient, sample_property: Property
):
    """Listed favorites include full property details."""
    await client.post(
        "/api/v1/favorites",
        json={"property_id": sample_property.id},
        headers={"X-Session-Token": TOKEN},
    )
    resp = await client.get(
        "/api/v1/favorites",
        headers={"X-Session-Token": TOKEN},
    )
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["id"] == sample_property.id
    assert items[0]["city"] == sample_property.city


async def test_list_favorites_session_isolation(
    client: AsyncClient, multiple_properties: list
):
    """Each session only sees its own favorites."""
    p1, p2 = multiple_properties[0], multiple_properties[1]
    await client.post(
        "/api/v1/favorites",
        json={"property_id": p1.id},
        headers={"X-Session-Token": TOKEN},
    )
    await client.post(
        "/api/v1/favorites",
        json={"property_id": p2.id},
        headers={"X-Session-Token": TOKEN_B},
    )

    resp_a = await client.get("/api/v1/favorites", headers={"X-Session-Token": TOKEN})
    resp_b = await client.get("/api/v1/favorites", headers={"X-Session-Token": TOKEN_B})

    ids_a = {item["id"] for item in resp_a.json()}
    ids_b = {item["id"] for item in resp_b.json()}
    assert p1.id in ids_a and p2.id not in ids_a
    assert p2.id in ids_b and p1.id not in ids_b


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/favorites/count
# ═══════════════════════════════════════════════════════════════════════════════

async def test_favorites_count_empty(client: AsyncClient):
    """Count returns 0 when no favorites."""
    resp = await client.get(
        "/api/v1/favorites/count",
        headers={"X-Session-Token": TOKEN},
    )
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


async def test_favorites_count_increments(
    client: AsyncClient, multiple_properties: list
):
    """Count increments as favorites are added."""
    for prop in multiple_properties[:3]:
        await client.post(
            "/api/v1/favorites",
            json={"property_id": prop.id},
            headers={"X-Session-Token": TOKEN},
        )
    resp = await client.get(
        "/api/v1/favorites/count",
        headers={"X-Session-Token": TOKEN},
    )
    assert resp.json()["count"] == 3


# ═══════════════════════════════════════════════════════════════════════════════
# DELETE /api/v1/favorites/{property_id}
# ═══════════════════════════════════════════════════════════════════════════════

async def test_delete_favorite_success(
    client: AsyncClient, sample_property: Property
):
    """Deleting an existing favorite returns 204."""
    await client.post(
        "/api/v1/favorites",
        json={"property_id": sample_property.id},
        headers={"X-Session-Token": TOKEN},
    )
    resp = await client.delete(
        f"/api/v1/favorites/{sample_property.id}",
        headers={"X-Session-Token": TOKEN},
    )
    assert resp.status_code == 204


async def test_delete_favorite_removes_from_list(
    client: AsyncClient, sample_property: Property
):
    """After deletion, the property no longer appears in the favorites list."""
    headers = {"X-Session-Token": TOKEN}
    await client.post(
        "/api/v1/favorites",
        json={"property_id": sample_property.id},
        headers=headers,
    )
    await client.delete(f"/api/v1/favorites/{sample_property.id}", headers=headers)
    resp = await client.get("/api/v1/favorites", headers=headers)
    assert resp.json() == []


async def test_delete_nonexistent_favorite_returns_404(client: AsyncClient):
    """Deleting a favorite that doesn't exist returns 404."""
    resp = await client.delete(
        "/api/v1/favorites/99999",
        headers={"X-Session-Token": TOKEN},
    )
    assert resp.status_code == 404
