"""
Answer endpoints.

Handles creating answers with their first version, adding new versions
(revisions), and retrieving answer details.

Pre-auth: user_id is not required — the evaluation flow works without
authentication. Auth is added in Milestone 7.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Answer, AnswerVersion, CompanyProfile, Evaluation, Question
from app.schemas.answers import (
    AnswerComparisonResponse,
    AnswerCreateRequest,
    AnswerDetailResponse,
    AnswerResponse,
    AnswerVersionResponse,
    VersionCreateRequest,
    VersionScoreSummary,
)

router = APIRouter(prefix="/api/v1/answers", tags=["answers"])


@router.post("", response_model=AnswerResponse, status_code=201)
async def create_answer(
    request: AnswerCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new answer with its first version.

    The answer links a question + company/role/level context.
    The first AnswerVersion is created automatically with the
    provided answer_text.

    Either question_id or custom_question_text must be provided.
    """
    # Validate: need either question_id or custom_question_text
    if not request.question_id and not request.custom_question_text:
        raise HTTPException(
            status_code=422,
            detail="Either question_id or custom_question_text must be provided",
        )

    # Validate company exists
    company_result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.id == request.target_company_id)
    )
    if not company_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Company not found")

    # Validate question exists (if provided)
    if request.question_id:
        q_result = await db.execute(
            select(Question).where(Question.id == request.question_id)
        )
        if not q_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Question not found")

    # Calculate word count
    word_count = len(request.answer_text.split())

    # Create answer
    answer = Answer(
        user_id=None,  # Pre-auth: no user
        question_id=request.question_id,
        custom_question_text=request.custom_question_text,
        target_company_id=request.target_company_id,
        target_role=request.target_role,
        experience_level=request.experience_level,
        version_count=1,
    )
    db.add(answer)
    await db.flush()  # Get the answer.id before creating version

    # Create first version
    version = AnswerVersion(
        answer_id=answer.id,
        version_number=1,
        answer_text=request.answer_text,
        word_count=word_count,
        is_ai_assisted=request.is_ai_assisted,
    )
    db.add(version)
    await db.commit()
    await db.refresh(answer)

    return AnswerResponse.model_validate(answer)


@router.get("/{answer_id}", response_model=AnswerDetailResponse)
async def get_answer(answer_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get an answer with all its versions.

    Returns the answer metadata plus all versions ordered by version_number.
    Each version includes its evaluation status/scores if evaluated.
    """
    result = await db.execute(
        select(Answer)
        .where(Answer.id == answer_id)
        .options(selectinload(Answer.versions))
    )
    answer = result.scalar_one_or_none()

    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    return AnswerDetailResponse.model_validate(answer)


@router.post(
    "/{answer_id}/versions",
    response_model=AnswerVersionResponse,
    status_code=201,
)
async def create_version(
    answer_id: UUID,
    request: VersionCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Add a new version (revision) to an existing answer.

    Used when the user revises their answer after reading feedback.
    The version_number auto-increments based on existing versions.
    """
    # Load answer
    result = await db.execute(
        select(Answer).where(Answer.id == answer_id)
    )
    answer = result.scalar_one_or_none()

    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    # Determine next version number
    next_version = answer.version_count + 1
    word_count = len(request.answer_text.split())

    # Create new version
    version = AnswerVersion(
        answer_id=answer.id,
        version_number=next_version,
        answer_text=request.answer_text,
        word_count=word_count,
        is_ai_assisted=request.is_ai_assisted,
    )
    db.add(version)

    # Update answer's version count
    answer.version_count = next_version

    await db.commit()
    await db.refresh(version)

    return AnswerVersionResponse.model_validate(version)


@router.get("/{answer_id}/compare", response_model=AnswerComparisonResponse)
async def compare_versions(
    answer_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get an answer with all version scores for side-by-side comparison.

    Returns each version's latest completed evaluation scores, making it
    easy for the frontend to render score deltas and improvement tracking.
    """
    # Load answer with versions (eager load)
    result = await db.execute(
        select(Answer)
        .where(Answer.id == answer_id)
        .options(
            selectinload(Answer.versions).selectinload(AnswerVersion.evaluations)
        )
    )
    answer = result.scalar_one_or_none()

    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    # Build version score summaries
    version_scores = []
    for version in sorted(answer.versions, key=lambda v: v.version_number):
        # Find the latest completed evaluation for this version
        completed_evals = [
            e for e in version.evaluations if e.status == "completed"
        ]
        completed_evals.sort(key=lambda e: e.created_at, reverse=True)
        latest_eval = completed_evals[0] if completed_evals else None

        summary = VersionScoreSummary(
            id=version.id,
            version_number=version.version_number,
            word_count=version.word_count,
            is_ai_assisted=version.is_ai_assisted,
            created_at=version.created_at,
            evaluation_id=latest_eval.id if latest_eval else None,
            evaluation_status=latest_eval.status if latest_eval else None,
            situation_score=latest_eval.situation_score if latest_eval else None,
            task_score=latest_eval.task_score if latest_eval else None,
            action_score=latest_eval.action_score if latest_eval else None,
            result_score=latest_eval.result_score if latest_eval else None,
            engagement_score=latest_eval.engagement_score if latest_eval else None,
            overall_score=latest_eval.overall_score if latest_eval else None,
            average_score=latest_eval.average_score if latest_eval else None,
        )
        version_scores.append(summary)

    return AnswerComparisonResponse(
        id=answer.id,
        user_id=answer.user_id,
        question_id=answer.question_id,
        custom_question_text=answer.custom_question_text,
        target_company_id=answer.target_company_id,
        target_role=answer.target_role,
        experience_level=answer.experience_level,
        version_count=answer.version_count,
        best_average_score=answer.best_average_score,
        created_at=answer.created_at,
        updated_at=answer.updated_at,
        version_scores=version_scores,
    )
