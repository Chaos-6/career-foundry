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

    Supports both standard STAR and agentic evaluation types.
    The evaluation_type field tells the frontend which score/display
    format to use.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    answer_version_id: UUID
    answer_id: Optional[UUID] = None  # parent answer — needed for revision flow
    answer_text: Optional[str] = None  # the answer text that was evaluated
    version_number: Optional[int] = None
    question_id: Optional[UUID] = None  # source question — for "back to question" link
    question_text: Optional[str] = None  # resolved question text (bank or custom)
    status: str  # queued, analyzing, completed, failed
    evaluation_type: str = "standard"  # standard, agentic

    # Standard STAR scores (null for agentic evaluations)
    situation_score: Optional[int] = None
    task_score: Optional[int] = None
    action_score: Optional[int] = None
    result_score: Optional[int] = None
    engagement_score: Optional[int] = None
    overall_score: Optional[int] = None
    average_score: Optional[Decimal] = None

    # Agentic scores (null for standard evaluations)
    agentic_scores: Optional[dict[str, int]] = None  # {dimension: 0-100}
    agentic_result: Optional[dict[str, Any]] = None  # full JSON response
    hiring_decision: Optional[str] = None  # STRONG_HIRE, HIRE, BORDERLINE, REJECT

    # Full evaluation content (standard: markdown, agentic: null)
    evaluation_markdown: Optional[str] = None
    evaluation_sections: Optional[dict[str, Any]] = None

    # Company alignment (standard only)
    company_alignment: Optional[dict[str, Any]] = None

    # Follow-up questions (standard only)
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


# ---------------------------------------------------------------------------
# Suggestions schemas
# ---------------------------------------------------------------------------

class SuggestionItem(BaseModel):
    """A single improvement suggestion for a weak STAR dimension."""

    section: str  # "situation", "task", "action", "result", "engagement", "overall"
    suggestion: str  # Actionable improvement tip (2-3 sentences)
    example: str  # Concrete example of improvement (1-2 sentences)


class SuggestionsResponse(BaseModel):
    """Response from the inline suggestions endpoint."""

    suggestions: list[SuggestionItem]
    message: Optional[str] = None  # e.g. "All scores above 3 — no suggestions needed"
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


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
    evaluation_type: str = "standard"  # standard, agentic

    # Standard STAR scores
    situation_score: Optional[int] = None
    task_score: Optional[int] = None
    action_score: Optional[int] = None
    result_score: Optional[int] = None
    engagement_score: Optional[int] = None
    overall_score: Optional[int] = None
    average_score: Optional[Decimal] = None

    # Agentic scores
    agentic_scores: Optional[dict[str, int]] = None
    agentic_result: Optional[dict[str, Any]] = None
    hiring_decision: Optional[str] = None

    # Feedback content (redacted — no answer text)
    evaluation_markdown: Optional[str] = None
    evaluation_sections: Optional[dict[str, Any]] = None
    company_alignment: Optional[dict[str, Any]] = None
    follow_up_questions: Optional[list[dict[str, Any]]] = None

    # Minimal metadata
    created_at: datetime
