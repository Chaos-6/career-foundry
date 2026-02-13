"""Tests for health check endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """GET / returns service info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Behavioral Interview Answer Evaluator"
    assert data["status"] == "running"
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """GET /health returns database connectivity status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
