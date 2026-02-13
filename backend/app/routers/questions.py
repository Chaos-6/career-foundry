"""
Question bank endpoints.

Public (no auth required). Supports filtering by role, competency,
difficulty, and company. Also has a random question endpoint for
practice drills and mock interview mode.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Question
from app.schemas.questions import QuestionListResponse, QuestionResponse

router = APIRouter(prefix="/api/v1/questions", tags=["questions"])


@router.get("/random", response_model=QuestionResponse)
async def get_random_question(
    role: Optional[str] = None,
    competency: Optional[str] = None,
    difficulty: Optional[str] = None,
    level: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get a random question, optionally filtered.

    Used by mock interview mode and the 'surprise me' button.

    Filtering uses PostgreSQL JSONB containment: the @> operator checks
    if the JSONB array contains the specified value.
    """
    query = select(Question).where(Question.is_active == True)  # noqa: E712

    if role:
        # JSONB containment: role_tags @> '["MLE"]'
        query = query.where(Question.role_tags.contains([role]))
    if competency:
        query = query.where(Question.competency_tags.contains([competency]))
    if difficulty:
        query = query.where(Question.difficulty == difficulty)
    if level:
        query = query.where(Question.level_band == level)

    # ORDER BY RANDOM() LIMIT 1 — fine for <1000 rows
    query = query.order_by(func.random()).limit(1)

    result = await db.execute(query)
    question = result.scalar_one_or_none()

    if not question:
        raise HTTPException(status_code=404, detail="No questions match the filters")

    return QuestionResponse.model_validate(question)


@router.get("", response_model=QuestionListResponse)
async def list_questions(
    role: Optional[str] = None,
    competency: Optional[str] = None,
    difficulty: Optional[str] = None,
    level: Optional[str] = None,
    company: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List questions with filtering and pagination.

    Supports filtering by:
    - role: MLE, PM, TPM, EM
    - competency: conflict, leadership, technical_challenge, etc.
    - difficulty: standard, advanced, senior_plus
    - level: entry, mid, senior, staff, manager (level band)
    - company: Amazon, Meta, etc. (questions commonly asked at)
    - search: full-text search on question_text

    Results are ordered by usage_count (most popular first).
    """
    query = select(Question).where(Question.is_active == True)  # noqa: E712

    if role:
        query = query.where(Question.role_tags.contains([role]))
    if competency:
        query = query.where(Question.competency_tags.contains([competency]))
    if difficulty:
        query = query.where(Question.difficulty == difficulty)
    if level:
        query = query.where(Question.level_band == level)
    if company:
        query = query.where(Question.company_tags.contains([company]))
    if search:
        query = query.where(Question.question_text.ilike(f"%{search}%"))

    # Count total matching
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Fetch page, ordered by popularity then id for stable pagination
    query = query.order_by(Question.usage_count.desc(), Question.id).offset(skip).limit(limit)
    result = await db.execute(query)
    questions = result.scalars().all()

    return QuestionListResponse(
        items=[QuestionResponse.model_validate(q) for q in questions],
        total=total,
        skip=skip,
        limit=limit,
    )
