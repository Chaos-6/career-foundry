"""Pydantic schemas for company profile endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CompanyListItem(BaseModel):
    """Compact company info for list endpoints."""

    id: UUID
    name: str
    slug: str
    principle_type: str

    model_config = {"from_attributes": True}


class CompanyResponse(BaseModel):
    """Full company profile with principles and interview guidance."""

    id: UUID
    name: str
    slug: str
    principle_type: str
    principles: list[dict]
    interview_focus: str
    interview_tips: Optional[list] = None
    logo_url: Optional[str] = None
    last_verified_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
