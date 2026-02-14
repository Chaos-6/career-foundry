"""
Pydantic schemas for evaluation endpoints.

Evaluations are the product's core output: Claude's scored assessment
of a STAR-formatted behavioral interview answer. Each evaluation links
to a specific AnswerVersion and contains 6 dimension scores plus
structured sections.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class EvaluationCreateRequest(BaseModel):
    """Request to create and run a new evaluation.

    The answer_version_id links to the specific version of the answer
    to evaluate. The pipeline runs as a background task.
    """

    answer_version_id: UUID


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class EvaluationResponse(BaseModel):
    """Full evaluation response for the frontend.

    The frontend polls this endpoint until status transitions from
    'queued' or 'analyzing' to 'completed' or 'failed'.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    answer_version_id: UUID
    answer_id: Optional[UUID] = None  # parent answer — needed for revision flow
    answer_text: Optional[str] = None  # the answer text that was evaluated
    version_number: Optional[int] = None
    status: str  # queued, analyzing, completed, failed

    # Scores (null until completed)
    situation_score: Optional[int] = None
    task_score: Optional[int] = None
    action_score: Optional[int] = None
    result_score: Optional[int] = None
    engagement_score: Optional[int] = None
    overall_score: Optional[int] = None
    average_score: Optional[Decimal] = None

    # Full evaluation content
    evaluation_markdown: Optional[str] = None
    evaluation_sections: Optional[dict[str, Any]] = None

    # Company alignment
    company_alignment: Optional[dict[str, Any]] = None

    # Follow-up questions
    follow_up_questions: Optional[list[dict[str, Any]]] = None

    # Sharing
    share_token: Optional[UUID] = None
    shared_at: Optional[datetime] = None

    # Metadata
    model_used: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    processing_seconds: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Sharing schemas
# ---------------------------------------------------------------------------

class ShareResponse(BaseModel):
    """Response when sharing is enabled for an evaluation."""

    share_token: str
    share_url: str


class SharedEvaluationResponse(BaseModel):
    """Read-only public view of a shared evaluation.

    Intentionally excludes:
    - answer_text (privacy — the actual answer is the user's work)
    - coach_notes (confidential feedback)
    - user info (no PII leakage)
    - internal metadata (tokens, processing time)
    """

    model_config = ConfigDict(from_attributes=True)

    # Context (no user-identifying info)
    company_name: Optional[str] = None
    target_role: Optional[str] = None
    question_text: Optional[str] = None

    # Scores
    situation_score: Optional[int] = None
    task_score: Optional[int] = None
    action_score: Optional[int] = None
    result_score: Optional[int] = None
    engagement_score: Optional[int] = None
    overall_score: Optional[int] = None
    average_score: Optional[Decimal] = None

    # Feedback content (redacted — no answer text)
    evaluation_markdown: Optional[str] = None
    evaluation_sections: Optional[dict[str, Any]] = None
    company_alignment: Optional[dict[str, Any]] = None
    follow_up_questions: Optional[list[dict[str, Any]]] = None

    # Minimal metadata
    created_at: datetime
