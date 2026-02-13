"""Tests for the AI answer generator endpoint.

These tests mock the Anthropic API — we don't want to make real Claude calls
in CI. The mock returns a fake STAR answer to verify our endpoint wiring.
"""

from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


def _make_mock_anthropic_response(answer_text: str = None):
    """Create a mock Anthropic API response for the generator."""
    if answer_text is None:
        answer_text = (
            "At my previous company, our ML pipeline was processing "
            "over 10 million records daily but had a 12% failure rate. "
            "As the senior data engineer, I was tasked with diagnosing "
            "and resolving the reliability issues before our peak season. "
            "I implemented a comprehensive monitoring system using custom "
            "drift detection algorithms and set up automated alerts. I also "
            "refactored the data validation layer to catch edge cases early. "
            "Within three weeks, we reduced the failure rate from 12% to 0.3%, "
            "saving the company an estimated $200K per quarter in reprocessing costs."
        )
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=answer_text)]
    mock_response.usage = MagicMock(input_tokens=800, output_tokens=350)
    return mock_response


@pytest.mark.asyncio
@patch("app.services.generator.anthropic.Anthropic")
async def test_generate_answer(mock_anthropic_cls, client: AsyncClient):
    """POST /api/v1/generator returns a generated STAR answer."""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_mock_anthropic_response()
    mock_anthropic_cls.return_value = mock_client

    response = await client.post(
        "/api/v1/generator",
        json={
            "question_text": "Tell me about a time you improved a system's reliability.",
            "company_name": "Amazon",
            "target_role": "SDE",
            "experience_level": "senior",
            "situation_bullets": "- ML pipeline processing 10M records/day\n- 12% failure rate",
            "task_bullets": "- Diagnose root cause\n- Fix before peak season",
            "action_bullets": "- Built drift detection monitoring\n- Refactored validation layer",
            "result_bullets": "- Failure rate dropped from 12% to 0.3%\n- Saved $200K/quarter",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer_text" in data
    assert data["word_count"] > 0
    assert data["model_used"] == "claude-sonnet-4-20250514"
    assert data["input_tokens"] == 800
    assert data["output_tokens"] == 350

    # Verify the Anthropic client was called with correct params
    call_args = mock_client.messages.create.call_args
    assert call_args.kwargs["temperature"] == 0.5
    assert call_args.kwargs["max_tokens"] == 2000
    assert "Amazon" in call_args.kwargs["messages"][0]["content"]


@pytest.mark.asyncio
@patch("app.services.generator.anthropic.Anthropic")
async def test_generate_answer_includes_context(mock_anthropic_cls, client: AsyncClient):
    """POST /api/v1/generator passes all context to Claude."""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_mock_anthropic_response()
    mock_anthropic_cls.return_value = mock_client

    await client.post(
        "/api/v1/generator",
        json={
            "question_text": "Tell me about leading a cross-functional project.",
            "company_name": "Google",
            "target_role": "TPM",
            "experience_level": "L5",
            "situation_bullets": "- Merger integration with 3 teams",
            "task_bullets": "- Align on single platform",
            "action_bullets": "- Ran weekly syncs, built shared roadmap",
            "result_bullets": "- Delivered on time, promoted afterward",
        },
    )

    # Check the user message included all our context
    call_args = mock_client.messages.create.call_args
    user_msg = call_args.kwargs["messages"][0]["content"]
    assert "Google" in user_msg
    assert "TPM" in user_msg
    assert "L5" in user_msg
    assert "Merger integration" in user_msg
    assert "promoted afterward" in user_msg


@pytest.mark.asyncio
async def test_generate_answer_missing_fields(client: AsyncClient):
    """POST /api/v1/generator rejects incomplete requests."""
    response = await client.post(
        "/api/v1/generator",
        json={
            "question_text": "Tell me about a time you led a team.",
            "company_name": "Meta",
            # Missing required fields
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generate_answer_short_bullets(client: AsyncClient):
    """POST /api/v1/generator rejects bullet points that are too short."""
    response = await client.post(
        "/api/v1/generator",
        json={
            "question_text": "Tell me about a time you led a team.",
            "company_name": "Meta",
            "target_role": "PM",
            "experience_level": "mid",
            "situation_bullets": "x",  # Too short (min 5)
            "task_bullets": "- Fix it",
            "action_bullets": "- Did stuff",
            "result_bullets": "- It worked",
        },
    )
    assert response.status_code == 422
