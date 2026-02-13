"""Tests for company profile endpoints."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_companies(client: AsyncClient):
    """GET /api/v1/companies returns all seeded companies."""
    response = await client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should have our seeded companies (at least 20+)
    assert len(data) >= 20
    # Each item has compact fields
    first = data[0]
    assert "id" in first
    assert "name" in first
    assert "slug" in first
    assert "principle_type" in first
    # Compact list should NOT include full principles
    assert "principles" not in first


@pytest.mark.asyncio
async def test_get_company_detail(client: AsyncClient, test_company):
    """GET /api/v1/companies/{id} returns full company with principles."""
    response = await client.get(f"/api/v1/companies/{test_company.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_company.name
    assert data["slug"] == test_company.slug
    assert data["principle_type"] == "Core Values"
    assert isinstance(data["principles"], list)
    assert len(data["principles"]) == 2
    assert data["principles"][0]["name"] == "Excellence"
    assert data["interview_focus"] is not None


@pytest.mark.asyncio
async def test_get_company_not_found(client: AsyncClient):
    """GET /api/v1/companies/{id} returns 404 for nonexistent company."""
    fake_id = uuid.uuid4()
    response = await client.get(f"/api/v1/companies/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_companies_sorted_by_name(client: AsyncClient):
    """GET /api/v1/companies returns companies sorted alphabetically."""
    response = await client.get("/api/v1/companies")
    data = response.json()
    names = [c["name"] for c in data]
    assert names == sorted(names)
