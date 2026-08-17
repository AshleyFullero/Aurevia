"""
Tests for /api/v1/admin endpoints.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.property import Property


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/admin/overview
# ═══════════════════════════════════════════════════════════════════════════════

async def test_admin_overview_empty_db(client: AsyncClient):
    """Overview returns zero-state when no data exists."""
    resp = await client.get("/api/v1/admin/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_properties"] == 0
    assert data["waitlist_count"] == 0
    assert data["contact_count"] == 0


async def test_admin_overview_required_fields(client: AsyncClient):
    """Overview response contains all required top-level keys."""
    resp = await client.get("/api/v1/admin/overview")
    assert resp.status_code == 200
    required = [
        "total_properties", "active_properties", "inactive_properties",
        "waitlist_count", "contact_count", "by_city", "by_property_type",
    ]
    for field in required:
        assert field in resp.json(), f"Missing field: {field}"


async def test_admin_overview_counts_all_properties(
    client: AsyncClient, multiple_properties: list
):
    """total_properties includes all seeded properties."""
    resp = await client.get("/api/v1/admin/overview")
    assert resp.json()["total_properties"] == len(multiple_properties)


async def test_admin_overview_by_city_grouped(
    client: AsyncClient, multiple_properties: list
):
    """by_city groups properties correctly."""
    resp = await client.get("/api/v1/admin/overview")
    by_city = resp.json()["by_city"]
    assert isinstance(by_city, list)
    city_names = {item["city"] for item in by_city}
    assert "Austin" in city_names


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/admin/properties
# ═══════════════════════════════════════════════════════════════════════════════

async def test_admin_properties_returns_all(
    client: AsyncClient, multiple_properties: list
):
    """Admin properties list returns all properties by default."""
    resp = await client.get("/api/v1/admin/properties")
    assert resp.status_code == 200
    assert len(resp.json()) == len(multiple_properties)


async def test_admin_properties_filter_active(
    client: AsyncClient, multiple_properties: list
):
    """Filtering by is_active=true returns only active properties."""
    resp = await client.get("/api/v1/admin/properties", params={"is_active": True})
    assert resp.status_code == 200
    items = resp.json()
    assert all(item["is_active"] for item in items)


async def test_admin_properties_contains_id_and_address(
    client: AsyncClient, sample_property: Property
):
    """Each property row contains id, address, city."""
    resp = await client.get("/api/v1/admin/properties")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    item = items[0]
    assert "id" in item
    assert "address" in item
    assert "city" in item
    assert "is_active" in item


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/admin/waitlist
# ═══════════════════════════════════════════════════════════════════════════════

async def test_admin_waitlist_empty(client: AsyncClient):
    """Returns [] when no waitlist entries exist."""
    resp = await client.get("/api/v1/admin/waitlist")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_admin_waitlist_shows_emails(client: AsyncClient):
    """Waitlist entries include email addresses."""
    await client.post("/api/v1/waitlist", json={"email": "admin@test.com"})
    resp = await client.get("/api/v1/admin/waitlist")
    assert resp.status_code == 200
    emails = [entry["email"] for entry in resp.json()]
    assert "admin@test.com" in emails


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/admin/contacts
# ═══════════════════════════════════════════════════════════════════════════════

async def test_admin_contacts_empty(client: AsyncClient):
    """Returns [] when no contact submissions exist."""
    resp = await client.get("/api/v1/admin/contacts")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_admin_contacts_shows_submissions(client: AsyncClient):
    """Contact submissions appear in admin list."""
    await client.post("/api/v1/contact", json={
        "name": "Admin Test", "email": "admin@contact.com",
        "message": "Test contact submission for admin.",
    })
    resp = await client.get("/api/v1/admin/contacts")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["name"] == "Admin Test"


# ═══════════════════════════════════════════════════════════════════════════════
# PUT /api/v1/admin/properties/{id}/toggle
# ═══════════════════════════════════════════════════════════════════════════════

async def test_toggle_property_deactivates(
    client: AsyncClient, sample_property: Property
):
    """Toggling an active property deactivates it."""
    resp = await client.put(
        f"/api/v1/admin/properties/{sample_property.id}/toggle"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["is_active"] is False


async def test_toggle_property_reactivates(
    client: AsyncClient, sample_property: Property
):
    """Toggling twice returns the property to active."""
    await client.put(f"/api/v1/admin/properties/{sample_property.id}/toggle")
    resp = await client.put(f"/api/v1/admin/properties/{sample_property.id}/toggle")
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True


async def test_toggle_nonexistent_property_returns_404(client: AsyncClient):
    """Toggling a property that doesn't exist returns 404."""
    resp = await client.put("/api/v1/admin/properties/99999/toggle")
    assert resp.status_code == 404
