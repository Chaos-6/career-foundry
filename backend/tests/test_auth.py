"""Tests for authentication endpoints."""

import uuid

import pytest
from httpx import AsyncClient


def _unique_email() -> str:
    """Generate a unique email for each test to avoid conflicts."""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    """POST /auth/register creates account and returns tokens."""
    response = await client.post(
        "/auth/register",
        json={
            "email": _unique_email(),
            "password": "securepassword123",
            "display_name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """POST /auth/register with existing email returns 409."""
    email = _unique_email()
    # Register first
    await client.post(
        "/auth/register",
        json={"email": email, "password": "securepassword123"},
    )
    # Try again with same email
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": "differentpassword"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    """POST /auth/login with correct credentials returns tokens."""
    email = _unique_email()
    await client.post(
        "/auth/register",
        json={"email": email, "password": "securepassword123"},
    )
    response = await client.post(
        "/auth/login",
        json={"email": email, "password": "securepassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """POST /auth/login with wrong password returns 401."""
    email = _unique_email()
    await client.post(
        "/auth/register",
        json={"email": email, "password": "securepassword123"},
    )
    response = await client.post(
        "/auth/login",
        json={"email": email, "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email(client: AsyncClient):
    """POST /auth/login with unknown email returns 401."""
    response = await client.post(
        "/auth/login",
        json={"email": _unique_email(), "password": "somepassword123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    """GET /auth/me with valid token returns user profile."""
    email = _unique_email()
    reg_resp = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "securepassword123",
            "display_name": "Me Test",
        },
    )
    token = reg_resp.json()["access_token"]

    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert data["display_name"] == "Me Test"
    assert data["plan_tier"] == "free"


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient):
    """GET /auth/me without token returns 401 or 403."""
    response = await client.get("/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    """POST /auth/refresh with valid refresh token returns new pair."""
    reg_resp = await client.post(
        "/auth/register",
        json={"email": _unique_email(), "password": "securepassword123"},
    )
    refresh_token = reg_resp.json()["refresh_token"]

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_with_access_token_fails(client: AsyncClient):
    """POST /auth/refresh with access token (wrong type) returns 401."""
    reg_resp = await client.post(
        "/auth/register",
        json={"email": _unique_email(), "password": "securepassword123"},
    )
    access_token = reg_resp.json()["access_token"]

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert response.status_code == 401
