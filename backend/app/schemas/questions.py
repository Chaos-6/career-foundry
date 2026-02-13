"""Pydantic schemas for question endpoints."""

from uuid import UUID

from pydantic import BaseModel


class QuestionResponse(BaseModel):
    """A behavioral interview question with metadata."""

    id: UUID
    question_text: str
    role_tags: list[str]
    company_tags: list[str]
    competency_tags: list[str]
    difficulty: str
    level_band: str | None = None
    usage_count: int

    model_config = {"from_attributes": True}


class QuestionListResponse(BaseModel):
    """Paginated list of questions."""

    items: list[QuestionResponse]
    total: int
    skip: int
    limit: int
