"""Tests for mock interview session endpoints."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_start_mock_session(client: AsyncClient, test_question):
    """POST /api/v1/mock creates a mock session with time limit."""
    response = await client.post(
        "/api/v1/mock",
        json={
            "question_id": str(test_question.id),
            "time_limit_seconds": 180,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["question_id"] == str(test_question.id)
    assert data["question_text"] == test_question.question_text
    assert data["time_limit_seconds"] == 180
    assert data["time_used_seconds"] is None
    assert data["completed"] is False


@pytest.mark.asyncio
async def test_start_mock_session_custom_time(client: AsyncClient, test_question):
    """POST /api/v1/mock allows custom time limits within bounds."""
    response = await client.post(
        "/api/v1/mock",
        json={
            "question_id": str(test_question.id),
            "time_limit_seconds": 300,
        },
    )
    assert response.status_code == 201
    assert response.json()["time_limit_seconds"] == 300


@pytest.mark.asyncio
async def test_start_mock_session_invalid_question(client: AsyncClient):
    """POST /api/v1/mock with nonexistent question returns 404."""
    response = await client.post(
        "/api/v1/mock",
        json={
            "question_id": str(uuid.uuid4()),
            "time_limit_seconds": 180,
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_start_mock_session_time_too_short(client: AsyncClient, test_question):
    """POST /api/v1/mock rejects time limits below 60 seconds."""
    response = await client.post(
        "/api/v1/mock",
        json={
            "question_id": str(test_question.id),
            "time_limit_seconds": 30,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_start_mock_session_time_too_long(client: AsyncClient, test_question):
    """POST /api/v1/mock rejects time limits above 600 seconds."""
    response = await client.post(
        "/api/v1/mock",
        json={
            "question_id": str(test_question.id),
            "time_limit_seconds": 900,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_complete_mock_session(client: AsyncClient, test_question):
    """PATCH /api/v1/mock/{id} marks session as completed with timing."""
    # Start session
    start_resp = await client.post(
        "/api/v1/mock",
        json={
            "question_id": str(test_question.id),
            "time_limit_seconds": 180,
        },
    )
    session_id = start_resp.json()["id"]

    # Complete it
    complete_resp = await client.patch(
        f"/api/v1/mock/{session_id}",
        json={"time_used_seconds": 145},
    )
    assert complete_resp.status_code == 200
    data = complete_resp.json()
    assert data["completed"] is True
    assert data["time_used_seconds"] == 145
    assert data["time_limit_seconds"] == 180


@pytest.mark.asyncio
async def test_complete_mock_session_not_found(client: AsyncClient):
    """PATCH /api/v1/mock/{id} returns 404 for nonexistent session."""
    response = await client.patch(
        f"/api/v1/mock/{uuid.uuid4()}",
        json={"time_used_seconds": 100},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_complete_mock_session_with_references(
    client: AsyncClient, test_question, test_answer_version, test_evaluation
):
    """PATCH /api/v1/mock/{id} can include answer_version_id and evaluation_id."""
    # Start session
    start_resp = await client.post(
        "/api/v1/mock",
        json={
            "question_id": str(test_question.id),
            "time_limit_seconds": 180,
        },
    )
    session_id = start_resp.json()["id"]

    # Complete with references to the answer version and evaluation
    complete_resp = await client.patch(
        f"/api/v1/mock/{session_id}",
        json={
            "time_used_seconds": 160,
            "answer_version_id": str(test_answer_version.id),
            "evaluation_id": str(test_evaluation.id),
        },
    )
    assert complete_resp.status_code == 200
    assert complete_resp.json()["completed"] is True
