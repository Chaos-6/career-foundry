"""
Pydantic schemas for answer and answer version endpoints.

Answers are the core data unit: a user's response to a behavioral question
in the context of a specific company/role/level. Each answer can have
multiple versions (revisions) tracked by AnswerVersion.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class AnswerCreateRequest(BaseModel):
    """Request to create a new answer with its first version.

    Either question_id (from the question bank) or custom_question_text
    must be provided. The company_id links to a CompanyProfile for
    evaluation context.
    """

    question_id: Optional[UUID] = None
    custom_question_text: Optional[str] = None
    target_company_id: UUID
    target_role: str = Field(..., min_length=1, max_length=50)
    experience_level: str = Field(..., min_length=1, max_length=50)
    answer_text: str = Field(..., min_length=10)
    is_ai_assisted: bool = False


class VersionCreateRequest(BaseModel):
    """Request to add a new version (revision) to an existing answer."""

    answer_text: str = Field(..., min_length=10)
    is_ai_assisted: bool = False


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class AnswerVersionResponse(BaseModel):
    """A single version of an answer."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    answer_id: UUID
    version_number: int
    answer_text: str
    word_count: Optional[int] = None
    is_ai_assisted: bool
    created_at: datetime


class AnswerResponse(BaseModel):
    """An answer with metadata (no versions included)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: Optional[UUID] = None
    question_id: Optional[UUID] = None
    custom_question_text: Optional[str] = None
    target_company_id: UUID
    target_role: str
    experience_level: str
    version_count: int
    best_average_score: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime


class AnswerDetailResponse(AnswerResponse):
    """An answer with all versions included."""

    versions: list[AnswerVersionResponse] = []


class VersionScoreSummary(BaseModel):
    """A version with its evaluation scores for comparison display."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_number: int
    word_count: Optional[int] = None
    is_ai_assisted: bool
    created_at: datetime
    # Evaluation scores (from the latest evaluation of this version)
    evaluation_id: Optional[UUID] = None
    evaluation_status: Optional[str] = None
    situation_score: Optional[int] = None
    task_score: Optional[int] = None
    action_score: Optional[int] = None
    result_score: Optional[int] = None
    engagement_score: Optional[int] = None
    overall_score: Optional[int] = None
    average_score: Optional[Decimal] = None


class AnswerComparisonResponse(AnswerResponse):
    """An answer with version score summaries for side-by-side comparison."""

    version_scores: list[VersionScoreSummary] = []


# ---------------------------------------------------------------------------
# Import schemas
# ---------------------------------------------------------------------------

class ImportAnswerItem(BaseModel):
    """A single answer created during bulk import."""

    answer_id: UUID
    question_text: Optional[str] = None
    word_count: int


class ImportResponse(BaseModel):
    """Response from the bulk import endpoint."""

    imported_count: int
    total_found: int
    answers: list[ImportAnswerItem]
    errors: list[str] = []
