"""Tests for question bank endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_questions_default(client: AsyncClient):
    """GET /api/v1/questions returns paginated questions."""
    response = await client.get("/api/v1/questions")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert data["total"] >= 40  # At least our seeded questions
    assert len(data["items"]) <= 20  # Default page size


@pytest.mark.asyncio
async def test_list_questions_filter_by_role(client: AsyncClient):
    """GET /api/v1/questions?role=MLE filters by role tag."""
    response = await client.get("/api/v1/questions?role=MLE")
    assert response.status_code == 200
    data = response.json()
    # All returned questions should have MLE in role_tags
    for q in data["items"]:
        assert "MLE" in q["role_tags"], f"Question missing MLE tag: {q['question_text'][:50]}"


@pytest.mark.asyncio
async def test_list_questions_filter_by_difficulty(client: AsyncClient):
    """GET /api/v1/questions?difficulty=advanced filters by difficulty."""
    response = await client.get("/api/v1/questions?difficulty=advanced")
    assert response.status_code == 200
    data = response.json()
    for q in data["items"]:
        assert q["difficulty"] == "advanced"


@pytest.mark.asyncio
async def test_list_questions_filter_by_competency(client: AsyncClient):
    """GET /api/v1/questions?competency=conflict_resolution filters by competency tag."""
    response = await client.get("/api/v1/questions?competency=conflict_resolution")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for q in data["items"]:
        assert "conflict_resolution" in q["competency_tags"]


@pytest.mark.asyncio
async def test_list_questions_search(client: AsyncClient):
    """GET /api/v1/questions?search=feedback finds questions by text."""
    response = await client.get("/api/v1/questions?search=feedback")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for q in data["items"]:
        assert "feedback" in q["question_text"].lower()


@pytest.mark.asyncio
async def test_list_questions_pagination(client: AsyncClient):
    """GET /api/v1/questions supports skip/limit pagination."""
    # Get first page
    r1 = await client.get("/api/v1/questions?limit=5&skip=0")
    d1 = r1.json()
    assert len(d1["items"]) == 5

    # Get second page
    r2 = await client.get("/api/v1/questions?limit=5&skip=5")
    d2 = r2.json()
    assert len(d2["items"]) == 5

    # Pages should be different
    ids1 = {q["id"] for q in d1["items"]}
    ids2 = {q["id"] for q in d2["items"]}
    assert ids1.isdisjoint(ids2), "Pages should not overlap"


@pytest.mark.asyncio
async def test_random_question(client: AsyncClient):
    """GET /api/v1/questions/random returns a single question."""
    response = await client.get("/api/v1/questions/random")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "question_text" in data
    assert "role_tags" in data


@pytest.mark.asyncio
async def test_random_question_with_role_filter(client: AsyncClient):
    """GET /api/v1/questions/random?role=EM returns an EM question."""
    response = await client.get("/api/v1/questions/random?role=EM")
    assert response.status_code == 200
    data = response.json()
    assert "EM" in data["role_tags"]


@pytest.mark.asyncio
async def test_list_questions_filter_by_level(client: AsyncClient):
    """GET /api/v1/questions?level=mid filters by level_band."""
    response = await client.get("/api/v1/questions?level=mid")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for q in data["items"]:
        assert q["level_band"] == "mid"


@pytest.mark.asyncio
async def test_list_questions_level_response_field(client: AsyncClient):
    """Questions include the level_band field in the response."""
    response = await client.get("/api/v1/questions?limit=5")
    assert response.status_code == 200
    data = response.json()
    for q in data["items"]:
        assert "level_band" in q  # Field exists (may be null for legacy)


@pytest.mark.asyncio
async def test_random_question_with_level_filter(client: AsyncClient):
    """GET /api/v1/questions/random?level=mid returns a mid-level question."""
    response = await client.get("/api/v1/questions/random?level=mid")
    assert response.status_code == 200
    data = response.json()
    assert data["level_band"] == "mid"


@pytest.mark.asyncio
async def test_random_question_no_match(client: AsyncClient):
    """GET /api/v1/questions/random with impossible filters returns 404."""
    response = await client.get("/api/v1/questions/random?role=CEO&difficulty=impossible")
    assert response.status_code == 404
