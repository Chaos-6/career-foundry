"""
Dashboard endpoints — user statistics and recent evaluations.

All endpoints require authentication.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Answer, AnswerVersion, Evaluation, User

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


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
