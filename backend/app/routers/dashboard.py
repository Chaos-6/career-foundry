"""
Dashboard endpoints — user statistics, recent evaluations, and score history.

All endpoints require authentication. The frontend Dashboard page calls
these endpoints to render personalized stats, recent activity, and
score trend charts.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Answer, AnswerVersion, CompanyProfile, Evaluation, Question, User

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class DashboardStats(BaseModel):
    """Summary statistics for the user's dashboard."""

    total_evaluations: int
    average_score: float | None
    best_score: float | None
    total_answers: int
    evaluations_this_month: int


class RecentEvaluation(BaseModel):
    """A recent evaluation for the dashboard list."""

    evaluation_id: str
    answer_id: str
    question_text: str | None
    company_name: str | None
    target_role: str
    average_score: float | None
    status: str
    created_at: str
    version_number: int | None = None


class ScoreDataPoint(BaseModel):
    """A single point on the score trend chart.

    Each point represents one completed evaluation, with its date,
    dimension scores, and contextual metadata.
    """

    evaluation_id: str
    date: str  # ISO date string
    situation: int | None = None
    task: int | None = None
    action: int | None = None
    result: int | None = None
    engagement: int | None = None
    overall: int | None = None
    average: float | None = None
    company_name: str | None = None
    target_role: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get summary statistics for the authenticated user's dashboard."""
    # Count total answers
    answer_count_result = await db.execute(
        select(func.count(Answer.id)).where(Answer.user_id == user.id)
    )
    total_answers = answer_count_result.scalar() or 0

    # Get evaluation stats through answer → version → evaluation chain
    eval_stats_query = (
        select(
            func.count(Evaluation.id),
            func.avg(Evaluation.average_score),
            func.max(Evaluation.average_score),
        )
        .join(AnswerVersion, Evaluation.answer_version_id == AnswerVersion.id)
        .join(Answer, AnswerVersion.answer_id == Answer.id)
        .where(Answer.user_id == user.id, Evaluation.status == "completed")
    )
    eval_result = await db.execute(eval_stats_query)
    row = eval_result.one()
    total_evals = row[0] or 0
    avg_score = round(float(row[1]), 1) if row[1] else None
    best_score = round(float(row[2]), 1) if row[2] else None

    return DashboardStats(
        total_evaluations=total_evals,
        average_score=avg_score,
        best_score=best_score,
        total_answers=total_answers,
        evaluations_this_month=user.evaluations_this_month,
    )


@router.get("/recent", response_model=list[RecentEvaluation])
async def get_recent_evaluations(
    limit: int = Query(default=10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the user's most recent evaluations with context.

    Returns evaluations ordered by creation date (newest first).
    Each entry includes the question text, company name, and scores
    so the dashboard can render a useful activity list.
    """
    # Join chain: Evaluation → AnswerVersion → Answer → Company/Question
    query = (
        select(
            Evaluation,
            AnswerVersion.version_number,
            Answer.id.label("answer_id"),
            Answer.target_role,
            Answer.custom_question_text,
            Answer.question_id,
            CompanyProfile.name.label("company_name"),
        )
        .join(AnswerVersion, Evaluation.answer_version_id == AnswerVersion.id)
        .join(Answer, AnswerVersion.answer_id == Answer.id)
        .join(CompanyProfile, Answer.target_company_id == CompanyProfile.id)
        .where(Answer.user_id == user.id)
        .order_by(Evaluation.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    rows = result.all()

    # Batch-load question texts for rows that reference the question bank
    question_ids = {r.question_id for r in rows if r.question_id}
    question_map: dict[str, str] = {}
    if question_ids:
        q_result = await db.execute(
            select(Question.id, Question.question_text).where(
                Question.id.in_(question_ids)
            )
        )
        question_map = {str(row.id): row.question_text for row in q_result.all()}

    recent = []
    for row in rows:
        ev: Evaluation = row[0]
        q_text = row.custom_question_text
        if not q_text and row.question_id:
            q_text = question_map.get(str(row.question_id))

        recent.append(
            RecentEvaluation(
                evaluation_id=str(ev.id),
                answer_id=str(row.answer_id),
                question_text=q_text,
                company_name=row.company_name,
                target_role=row.target_role,
                average_score=(
                    round(float(ev.average_score), 1) if ev.average_score else None
                ),
                status=ev.status,
                created_at=ev.created_at.isoformat(),
                version_number=row.version_number,
            )
        )

    return recent


@router.get("/score-history", response_model=list[ScoreDataPoint])
async def get_score_history(
    limit: int = Query(default=30, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get chronological score data for trend visualization.

    Returns completed evaluations ordered by date (oldest first) so the
    frontend can render a line/area chart showing score progression.
    """
    query = (
        select(
            Evaluation,
            CompanyProfile.name.label("company_name"),
            Answer.target_role,
        )
        .join(AnswerVersion, Evaluation.answer_version_id == AnswerVersion.id)
        .join(Answer, AnswerVersion.answer_id == Answer.id)
        .join(CompanyProfile, Answer.target_company_id == CompanyProfile.id)
        .where(Answer.user_id == user.id, Evaluation.status == "completed")
        .order_by(Evaluation.created_at.asc())
        .limit(limit)
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        ScoreDataPoint(
            evaluation_id=str(row[0].id),
            date=row[0].created_at.isoformat(),
            situation=row[0].situation_score,
            task=row[0].task_score,
            action=row[0].action_score,
            result=row[0].result_score,
            engagement=row[0].engagement_score,
            overall=row[0].overall_score,
            average=(
                round(float(row[0].average_score), 1)
                if row[0].average_score
                else None
            ),
            company_name=row.company_name,
            target_role=row.target_role,
        )
        for row in rows
    ]
