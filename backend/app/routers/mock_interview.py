"""
Mock interview endpoints.

Manages timed practice sessions where the user answers under time pressure.
The timer runs on the frontend; the backend tracks session metadata.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import MockSession, Question

router = APIRouter(prefix="/api/v1/mock", tags=["mock-interview"])


class MockSessionCreate(BaseModel):
    """Request to start a mock interview session."""

    question_id: UUID
    time_limit_seconds: int = Field(default=180, ge=60, le=600)


class MockSessionResponse(BaseModel):
    """Mock session metadata."""

    id: str
    question_id: str
    question_text: str
    time_limit_seconds: int
    time_used_seconds: int | None
    completed: bool


class MockSessionComplete(BaseModel):
    """Request to mark a mock session as complete."""

    time_used_seconds: int
    answer_version_id: UUID | None = None
    evaluation_id: UUID | None = None


@router.post("", response_model=MockSessionResponse, status_code=201)
async def start_mock_session(
    request: MockSessionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Start a new mock interview session.

    Returns the question and time limit. The frontend manages the timer
    and submits the answer when time expires or the user finishes.
    """
    # Load question
    q_result = await db.execute(
        select(Question).where(Question.id == request.question_id)
    )
    question = q_result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Create session
    session_record = MockSession(
        user_id=None,  # Pre-auth
        question_id=request.question_id,
        time_limit_seconds=request.time_limit_seconds,
    )
    db.add(session_record)
    await db.commit()
    await db.refresh(session_record)

    return MockSessionResponse(
        id=str(session_record.id),
        question_id=str(question.id),
        question_text=question.question_text,
        time_limit_seconds=session_record.time_limit_seconds,
        time_used_seconds=None,
        completed=False,
    )


@router.patch("/{session_id}", response_model=MockSessionResponse)
async def complete_mock_session(
    session_id: UUID,
    request: MockSessionComplete,
    db: AsyncSession = Depends(get_db),
):
    """Mark a mock session as completed with timing data."""
    result = await db.execute(
        select(MockSession).where(MockSession.id == session_id)
    )
    session_record = result.scalar_one_or_none()
    if not session_record:
        raise HTTPException(status_code=404, detail="Mock session not found")

    session_record.time_used_seconds = request.time_used_seconds
    session_record.completed = True
    if request.answer_version_id:
        session_record.answer_version_id = request.answer_version_id
    if request.evaluation_id:
        session_record.evaluation_id = request.evaluation_id

    await db.commit()

    # Load question text for response
    q_result = await db.execute(
        select(Question).where(Question.id == session_record.question_id)
    )
    question = q_result.scalar_one_or_none()

    return MockSessionResponse(
        id=str(session_record.id),
        question_id=str(session_record.question_id),
        question_text=question.question_text if question else "",
        time_limit_seconds=session_record.time_limit_seconds,
        time_used_seconds=session_record.time_used_seconds,
        completed=True,
    )
