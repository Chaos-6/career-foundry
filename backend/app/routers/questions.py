"""
Question bank endpoints.

Public endpoints (no auth):
  GET  /random — random question for practice
  GET  /       — browse questions with filters

Authenticated endpoints:
  POST /       — submit a community question (goes to moderation queue)

Moderator endpoints:
  GET   /moderation/pending — list pending submissions
  PATCH /{id}/moderation    — approve or reject a submission
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_moderator
from app.models import Question, User
from app.services.email import (
    question_approved_email,
    question_rejected_email,
    send_email,
)
from app.schemas.questions import (
    ModerationActionRequest,
    QuestionListResponse,
    QuestionModerationResponse,
    QuestionResponse,
    QuestionSubmitRequest,
)

router = APIRouter(prefix="/api/v1/questions", tags=["questions"])


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

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
    Only returns approved questions (curated + approved community).
    """
    query = (
        select(Question)
        .where(Question.is_active == True)  # noqa: E712
        .where(Question.status == "approved")
    )

    if role:
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
    source: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List questions with filtering and pagination.

    Only returns approved questions. Community submissions that are
    still pending moderation won't appear here.

    Supports filtering by:
    - role: MLE, PM, TPM, EM
    - competency: conflict, leadership, technical_challenge, etc.
    - difficulty: standard, advanced, senior_plus
    - level: entry, mid, senior, staff, manager (level band)
    - company: Amazon, Meta, etc. (questions commonly asked at)
    - search: full-text search on question_text
    - source: curated, community (filter by origin)

    Results are ordered by usage_count (most popular first).
    """
    query = (
        select(Question)
        .where(Question.is_active == True)  # noqa: E712
        .where(Question.status == "approved")
    )

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
    if source:
        query = query.where(Question.source == source)

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


# ---------------------------------------------------------------------------
# Community submission (requires auth)
# ---------------------------------------------------------------------------

@router.post("", response_model=QuestionResponse, status_code=201)
async def submit_question(
    request: QuestionSubmitRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a community question for moderation.

    The question is created with status='pending' and source='community'.
    It won't appear in the public question bank until a moderator approves it.

    Returns the created question (with pending status).
    """
    # Basic duplicate check: same text from same user
    existing = await db.execute(
        select(Question).where(
            Question.question_text == request.question_text,
            Question.submitted_by_user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="You've already submitted this question.",
        )

    question = Question(
        question_text=request.question_text,
        role_tags=request.role_tags,
        company_tags=request.company_tags,
        competency_tags=request.competency_tags,
        difficulty=request.difficulty,
        level_band=request.level_band,
        source="community",
        status="pending",
        submitted_by_user_id=user.id,
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)

    return QuestionResponse.model_validate(question)


# ---------------------------------------------------------------------------
# Moderation endpoints (requires moderator role)
# ---------------------------------------------------------------------------

@router.get(
    "/moderation/pending",
    response_model=list[QuestionModerationResponse],
)
async def list_pending_questions(
    skip: int = 0,
    limit: int = 50,
    moderator: User = Depends(get_moderator),
    db: AsyncSession = Depends(get_db),
):
    """List questions pending moderation.

    Only accessible to moderators. Returns submissions ordered
    by creation date (oldest first — FIFO queue).
    """
    query = (
        select(Question)
        .where(Question.status == "pending")
        .order_by(Question.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    questions = result.scalars().all()

    # Enrich with submitter email
    responses = []
    for q in questions:
        resp = QuestionModerationResponse.model_validate(q)
        if q.submitted_by_user_id:
            user_result = await db.execute(
                select(User.email).where(User.id == q.submitted_by_user_id)
            )
            resp.submitted_by_email = user_result.scalar_one_or_none()
        responses.append(resp)

    return responses


@router.patch(
    "/{question_id}/moderation",
    response_model=QuestionModerationResponse,
)
async def moderate_question(
    question_id: UUID,
    request: ModerationActionRequest,
    background_tasks: BackgroundTasks,
    moderator: User = Depends(get_moderator),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a pending community question.

    Only accessible to moderators.
    - approve: sets status to 'approved', question appears in public bank
    - reject: sets status to 'rejected', question stays hidden
    """
    result = await db.execute(
        select(Question).where(Question.id == question_id)
    )
    question = result.scalar_one_or_none()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    if question.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Question is already {question.status}",
        )

    if request.action == "reject" and not request.notes:
        raise HTTPException(
            status_code=400,
            detail="Rejection reason is required",
        )

    question.status = "approved" if request.action == "approve" else "rejected"
    question.moderation_notes = request.notes
    question.moderated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(question)

    # Build response with submitter email
    resp = QuestionModerationResponse.model_validate(question)
    if question.submitted_by_user_id:
        submitter_result = await db.execute(
            select(User).where(User.id == question.submitted_by_user_id)
        )
        submitter = submitter_result.scalar_one_or_none()
        if submitter:
            resp.submitted_by_email = submitter.email

            # Send notification email to submitter
            if getattr(submitter, "email_notifications", True):
                if request.action == "approve":
                    subject, html = question_approved_email(question.question_text)
                else:
                    subject, html = question_rejected_email(
                        question.question_text, request.notes or ""
                    )
                background_tasks.add_task(send_email, submitter.email, subject, html)

    return resp
