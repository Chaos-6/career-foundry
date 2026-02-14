"""Pydantic schemas for coaching/team endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Coaching relationship schemas
# ---------------------------------------------------------------------------

class InviteStudentRequest(BaseModel):
    """Coach invites a student by email."""

    email: EmailStr


class CoachingRelationshipResponse(BaseModel):
    """A coaching relationship with both parties' info."""

    id: UUID
    coach_id: UUID
    coach_email: str
    coach_name: str | None = None
    student_id: UUID
    student_email: str
    student_name: str | None = None
    status: str
    created_at: datetime | None = None
    accepted_at: datetime | None = None


class StudentSummary(BaseModel):
    """Summary of a student's progress, shown in the coach dashboard."""

    student_id: str
    email: str
    display_name: str | None = None
    avatar_url: str | None = None
    total_evaluations: int
    average_score: float | None = None
    best_score: float | None = None
    latest_evaluation_date: str | None = None
    relationship_id: str


class CoachDashboardResponse(BaseModel):
    """Aggregate data for the coach dashboard."""

    students: list[StudentSummary]
    total_students: int
    pending_invites: int


# ---------------------------------------------------------------------------
# Coach feedback on evaluations
# ---------------------------------------------------------------------------

class CoachNotesRequest(BaseModel):
    """Coach adding feedback to a student's evaluation."""

    notes: str = Field(..., min_length=1, max_length=2000)
    focus_areas: list[str] = Field(default_factory=list, max_length=10)


class CoachNotesResponse(BaseModel):
    """Coach notes attached to an evaluation."""

    notes: str
    focus_areas: list[str]
    coach_id: str
    coach_name: str | None = None
    updated_at: str | None = None
