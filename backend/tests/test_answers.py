"""Tests for answer and answer version endpoints."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_answer_with_question(
    client: AsyncClient, test_company, test_question
):
    """POST /api/v1/answers creates an answer with first version."""
    response = await client.post(
        "/api/v1/answers",
        json={
            "question_id": str(test_question.id),
            "target_company_id": str(test_company.id),
            "target_role": "MLE",
            "experience_level": "senior",
            "answer_text": (
                "Situation: At my previous company, we had a critical ML pipeline "
                "that was failing intermittently in production. "
                "Task: I was responsible for debugging the root cause and fixing it. "
                "Action: I analyzed the data distribution shift that was causing "
                "the model to underperform and implemented drift detection. "
                "Result: The model accuracy improved from 78% to 94%, and we "
                "reduced pipeline failures by 99%."
            ),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["target_role"] == "MLE"
    assert data["experience_level"] == "senior"
    assert data["version_count"] == 1
    assert data["question_id"] == str(test_question.id)
    assert data["target_company_id"] == str(test_company.id)


@pytest.mark.asyncio
async def test_create_answer_with_custom_question(
    client: AsyncClient, test_company
):
    """POST /api/v1/answers with custom question text works."""
    response = await client.post(
        "/api/v1/answers",
        json={
            "custom_question_text": "Tell me about a time you disagreed with your manager.",
            "target_company_id": str(test_company.id),
            "target_role": "PM",
            "experience_level": "mid",
            "answer_text": (
                "Situation: During a quarterly planning meeting, my manager "
                "proposed cutting the testing phase to meet a deadline. "
                "Task: I needed to advocate for quality without undermining authority. "
                "Action: I prepared data showing the cost of shipping bugs. "
                "Result: We compromised on automated testing, saving 2 weeks."
            ),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["custom_question_text"] == "Tell me about a time you disagreed with your manager."
    assert data["question_id"] is None


@pytest.mark.asyncio
async def test_create_answer_requires_question_or_custom(
    client: AsyncClient, test_company
):
    """POST /api/v1/answers without question_id or custom_question_text fails."""
    response = await client.post(
        "/api/v1/answers",
        json={
            "target_company_id": str(test_company.id),
            "target_role": "MLE",
            "experience_level": "senior",
            "answer_text": "Some answer text that is long enough to pass validation.",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_answer_invalid_company(
    client: AsyncClient, test_question
):
    """POST /api/v1/answers with nonexistent company returns 404."""
    response = await client.post(
        "/api/v1/answers",
        json={
            "question_id": str(test_question.id),
            "target_company_id": str(uuid.uuid4()),
            "target_role": "MLE",
            "experience_level": "senior",
            "answer_text": "Some answer text that is long enough to pass validation.",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_answer_detail(client: AsyncClient, test_answer):
    """GET /api/v1/answers/{id} returns answer with versions."""
    response = await client.get(f"/api/v1/answers/{test_answer.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_answer.id)
    assert data["target_role"] == "MLE"
    # Versions are populated from fixture chain
    assert isinstance(data["versions"], list)


@pytest.mark.asyncio
async def test_get_answer_not_found(client: AsyncClient):
    """GET /api/v1/answers/{id} returns 404 for nonexistent answer."""
    response = await client.get(f"/api/v1/answers/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_version(client: AsyncClient, test_company, test_question):
    """POST /api/v1/answers/{id}/versions adds a new revision."""
    # First create an answer
    create_resp = await client.post(
        "/api/v1/answers",
        json={
            "question_id": str(test_question.id),
            "target_company_id": str(test_company.id),
            "target_role": "MLE",
            "experience_level": "senior",
            "answer_text": "Version 1: Situation: At my company, we had a pipeline issue. "
                          "Task: I was responsible. Action: I fixed it. Result: It worked.",
        },
    )
    answer_id = create_resp.json()["id"]

    # Add version 2
    v2_resp = await client.post(
        f"/api/v1/answers/{answer_id}/versions",
        json={
            "answer_text": "Version 2: Situation: At my previous company, our ML pipeline "
                          "was failing due to data drift. Task: As the senior engineer, "
                          "I owned the investigation. Action: I implemented drift detection "
                          "monitoring. Result: Pipeline reliability improved from 78% to 99%.",
        },
    )
    assert v2_resp.status_code == 201
    v2_data = v2_resp.json()
    assert v2_data["version_number"] == 2
    assert v2_data["answer_id"] == answer_id

    # Verify answer detail now shows version_count=2
    detail_resp = await client.get(f"/api/v1/answers/{answer_id}")
    assert detail_resp.json()["version_count"] == 2


@pytest.mark.asyncio
async def test_compare_versions(
    client: AsyncClient, test_answer, test_answer_version, test_evaluation
):
    """GET /api/v1/answers/{id}/compare returns version score summaries."""
    response = await client.get(f"/api/v1/answers/{test_answer.id}/compare")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_answer.id)
    assert "version_scores" in data
    assert len(data["version_scores"]) >= 1

    # The test_evaluation fixture has scores for test_answer_version
    vs = data["version_scores"][0]
    assert vs["version_number"] == 1
    assert vs["evaluation_status"] == "completed"
    assert vs["situation_score"] == 4
    assert vs["task_score"] == 3
    assert vs["action_score"] == 4
    assert vs["result_score"] == 5
    assert float(vs["average_score"]) == 3.8
