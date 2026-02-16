"""Pydantic schemas for question endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class QuestionResponse(BaseModel):
    """A behavioral interview question with metadata."""

    id: UUID
    question_text: str
    role_tags: list[str]
    company_tags: list[str]
    competency_tags: list[str]
    difficulty: str
    level_band: str | None = None
    source: str = "curated"
    usage_count: int
    track: str = "standard"  # standard, agentic
    interview_type: str = "behavioral"  # behavioral, system_design
    tags: list[str] = []  # freeform tags
    ideal_answer_points: list[str] = []  # key points a good answer should hit

    model_config = {"from_attributes": True}


class QuestionListResponse(BaseModel):
    """Paginated list of questions."""

    items: list[QuestionResponse]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# Community question submission
# ---------------------------------------------------------------------------

class QuestionSubmitRequest(BaseModel):
    """Request to submit a community question for moderation."""

    question_text: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="The behavioral interview question text",
    )
    role_tags: list[str] = Field(default_factory=list, max_length=10)
    company_tags: list[str] = Field(default_factory=list, max_length=10)
    competency_tags: list[str] = Field(default_factory=list, max_length=10)
    difficulty: str = "standard"
    level_band: Optional[str] = None


class QuestionModerationResponse(BaseModel):
    """Full question details including moderation metadata.

    Used in the moderation queue — shows who submitted it, when,
    and the current moderation status.
    """

    id: UUID
    question_text: str
    role_tags: list[str]
    company_tags: list[str]
    competency_tags: list[str]
    difficulty: str
    level_band: str | None = None
    source: str
    status: str
    submitted_by_user_id: UUID | None = None
    submitted_by_email: str | None = None  # Joined from User table
    moderation_notes: str | None = None
    moderated_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ModerationActionRequest(BaseModel):
    """Request body for approve/reject moderation action."""

    action: str = Field(..., pattern="^(approve|reject)$")
    notes: Optional[str] = None  # Required for rejections, optional for approvals
