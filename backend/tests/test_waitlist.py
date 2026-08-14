"""
Tests for /api/v1/waitlist endpoints.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


# ── POST /api/v1/waitlist ─────────────────────────────────────────────────────

async def test_join_waitlist_success(client: AsyncClient):
    """Successfully joining waitlist returns 201 and a position."""
    resp = await client.post("/api/v1/waitlist", json={
        "email": "test@example.com",
        "source": "landing_page",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["email"] == "test@example.com"
    assert data["position"] == 1


async def test_join_waitlist_second_person_gets_position_2(client: AsyncClient):
    """Second signup gets position 2."""
    await client.post("/api/v1/waitlist", json={"email": "first@example.com"})
    resp = await client.post("/api/v1/waitlist", json={"email": "second@example.com"})
    assert resp.status_code == 201
    assert resp.json()["position"] == 2


async def test_join_waitlist_duplicate_email_returns_409(client: AsyncClient):
    """Duplicate email returns 409 Conflict."""
    await client.post("/api/v1/waitlist", json={"email": "dupe@example.com"})
    resp = await client.post("/api/v1/waitlist", json={"email": "dupe@example.com"})
    assert resp.status_code == 409
    assert "already on the waitlist" in resp.json()["detail"].lower()


async def test_join_waitlist_email_normalised_to_lowercase(client: AsyncClient):
    """Email addresses are normalised to lowercase."""
    resp = await client.post("/api/v1/waitlist", json={"email": "User@EXAMPLE.COM"})
    assert resp.status_code == 201
    assert resp.json()["email"] == "user@example.com"


async def test_join_waitlist_invalid_email_returns_422(client: AsyncClient):
    """Invalid email format returns 422 Unprocessable Entity."""
    resp = await client.post("/api/v1/waitlist", json={"email": "not-an-email"})
    assert resp.status_code == 422


async def test_join_waitlist_missing_email_returns_422(client: AsyncClient):
    """Missing email field returns 422."""
    resp = await client.post("/api/v1/waitlist", json={})
    assert resp.status_code == 422


async def test_join_waitlist_default_source(client: AsyncClient):
    """Source defaults to 'landing_page' when not provided."""
    resp = await client.post("/api/v1/waitlist", json={"email": "nosource@example.com"})
    assert resp.status_code == 201
    # Source isn't in the response schema, but the endpoint should succeed
    assert resp.json()["success"] is True


# ── GET /api/v1/waitlist/count ────────────────────────────────────────────────

async def test_waitlist_count_empty(client: AsyncClient):
    """Count returns 0 when no entries exist."""
    resp = await client.get("/api/v1/waitlist/count")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


async def test_waitlist_count_increments(client: AsyncClient):
    """Count increments correctly as entries are added."""
    for i in range(3):
        await client.post("/api/v1/waitlist", json={"email": f"user{i}@example.com"})

    resp = await client.get("/api/v1/waitlist/count")
    assert resp.status_code == 200
    assert resp.json()["count"] == 3


async def test_waitlist_count_has_unit_field(client: AsyncClient):
    """Count response includes a 'unit' field."""
    resp = await client.get("/api/v1/waitlist/count")
    assert resp.status_code == 200
    assert "unit" in resp.json()
