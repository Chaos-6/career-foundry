"""
Pydantic schemas for answer template endpoints.

Templates are reusable STAR answer frameworks that users save and load
into the evaluation form. Supports CRUD operations with optional filtering
by role and competency tags.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class TemplateCreateRequest(BaseModel):
    """Create a new answer template."""

    name: str = Field(..., min_length=1, max_length=255)
    template_text: str = Field(..., min_length=10)
    role_tags: list[str] = Field(default_factory=list)
    competency_tags: list[str] = Field(default_factory=list)
    is_default: bool = False


class TemplateUpdateRequest(BaseModel):
    """Update an existing template — all fields optional."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    template_text: Optional[str] = Field(None, min_length=10)
    role_tags: Optional[list[str]] = None
    competency_tags: Optional[list[str]] = None
    is_default: Optional[bool] = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class TemplateResponse(BaseModel):
    """Full template response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    template_text: str
    role_tags: list[str]
    competency_tags: list[str]
    is_default: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime


class TemplateListItem(BaseModel):
    """Lightweight template for list/dropdown views (no full text)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    role_tags: list[str]
    competency_tags: list[str]
    is_default: bool
    usage_count: int
    created_at: datetime
