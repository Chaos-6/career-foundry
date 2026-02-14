"""
Dashboard endpoints — user statistics, recent evaluations, and score history.

All endpoints require authentication. The frontend Dashboard page calls
these endpoints to render personalized stats, recent activity, and
score trend charts.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Answer, AnswerVersion, CompanyProfile, Evaluation, Question, User
from app.services.gamification import BADGE_DEFINITIONS

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class BadgeInfo(BaseModel):
    """A single badge with unlock status."""
    id: str
    name: str
    description: str
    icon: str
    unlocked: bool
    unlocked_at: str | None = None


class StreakInfo(BaseModel):
    """Practice streak data for the dashboard widget."""
    current_streak: int
    longest_streak: int
    last_practice_date: str | None
    streak_active: bool  # True if user practiced today or yesterday


class DashboardStats(BaseModel):
    """Summary statistics for the user's dashboard."""

    total_evaluations: int
    average_score: float | None
    best_score: float | None
    total_answers: int
    evaluations_this_month: int
    streak: StreakInfo | None = None
    badges: list[BadgeInfo] = []


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

    # Build streak info
    streak_active = False
    if user.last_practice_date:
        last_date = user.last_practice_date.date()
        today = datetime.now(timezone.utc).date()
        streak_active = last_date >= today - timedelta(days=1)

    streak_info = StreakInfo(
        current_streak=getattr(user, "current_streak", 0) or 0,
        longest_streak=getattr(user, "longest_streak", 0) or 0,
        last_practice_date=(
            user.last_practice_date.isoformat() if user.last_practice_date else None
        ),
        streak_active=streak_active,
    )

    # Build badge info — merge definitions with user's unlocked badges
    user_badges = {b["id"]: b for b in (getattr(user, "badges", None) or [])}
    badge_list = []
    for defn in BADGE_DEFINITIONS:
        unlocked = defn["id"] in user_badges
        badge_list.append(BadgeInfo(
            id=defn["id"],
            name=defn["name"],
            description=defn["description"],
            icon=defn["icon"],
            unlocked=unlocked,
            unlocked_at=user_badges[defn["id"]].get("unlocked_at") if unlocked else None,
        ))

    return DashboardStats(
        total_evaluations=total_evals,
        average_score=avg_score,
        best_score=best_score,
        total_answers=total_answers,
        evaluations_this_month=user.evaluations_this_month,
        streak=streak_info,
        badges=badge_list,
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


# ---------------------------------------------------------------------------
# Advanced analytics schemas
# ---------------------------------------------------------------------------

class DimensionAverage(BaseModel):
    """Average score for a single STAR dimension."""

    dimension: str
    average: float
    count: int


class CompanyBreakdown(BaseModel):
    """Aggregated scores for a specific company target."""

    company_name: str
    evaluation_count: int
    average_score: float | None
    best_score: float | None
    situation_avg: float | None
    task_avg: float | None
    action_avg: float | None
    result_avg: float | None
    engagement_avg: float | None
    overall_avg: float | None


class ReadinessScore(BaseModel):
    """Interview readiness calculation.

    Weights:
    - score_component (40%): avg score normalised to 0-100
    - consistency_component (30%): low std-dev across dimensions → high consistency
    - trend_component (30%): positive slope from first to last evaluation → improvement
    """

    overall_readiness: int  # 0-100
    score_component: int
    consistency_component: int
    trend_component: int
    label: str  # "Not Ready", "Getting There", "Interview Ready", "Strong Candidate"


class AnalyticsResponse(BaseModel):
    """All analytics data in a single response to minimise roundtrips."""

    dimension_averages: list[DimensionAverage]
    company_breakdowns: list[CompanyBreakdown]
    readiness: ReadinessScore | None


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Comprehensive analytics for the Advanced Analytics page.

    Returns:
    - Per-dimension averages (for radar chart)
    - Per-company breakdowns (for comparison table)
    - Interview readiness score (weighted composite)
    """
    # ── Per-dimension averages ──────────────────────────────────────────
    dim_query = (
        select(
            func.avg(Evaluation.situation_score),
            func.avg(Evaluation.task_score),
            func.avg(Evaluation.action_score),
            func.avg(Evaluation.result_score),
            func.avg(Evaluation.engagement_score),
            func.avg(Evaluation.overall_score),
            func.count(Evaluation.id),
        )
        .join(AnswerVersion, Evaluation.answer_version_id == AnswerVersion.id)
        .join(Answer, AnswerVersion.answer_id == Answer.id)
        .where(Answer.user_id == user.id, Evaluation.status == "completed")
    )
    dim_result = await db.execute(dim_query)
    dim_row = dim_result.one()
    total_count = dim_row[6] or 0

    dimension_names = [
        "Situation", "Task", "Action", "Result", "Engagement", "Overall"
    ]
    dimension_averages = []
    for i, name in enumerate(dimension_names):
        val = dim_row[i]
        dimension_averages.append(
            DimensionAverage(
                dimension=name,
                average=round(float(val), 2) if val else 0.0,
                count=total_count,
            )
        )

    # ── Per-company breakdowns ──────────────────────────────────────────
    company_query = (
        select(
            CompanyProfile.name,
            func.count(Evaluation.id),
            func.avg(Evaluation.average_score),
            func.max(Evaluation.average_score),
            func.avg(Evaluation.situation_score),
            func.avg(Evaluation.task_score),
            func.avg(Evaluation.action_score),
            func.avg(Evaluation.result_score),
            func.avg(Evaluation.engagement_score),
            func.avg(Evaluation.overall_score),
        )
        .join(AnswerVersion, Evaluation.answer_version_id == AnswerVersion.id)
        .join(Answer, AnswerVersion.answer_id == Answer.id)
        .join(CompanyProfile, Answer.target_company_id == CompanyProfile.id)
        .where(Answer.user_id == user.id, Evaluation.status == "completed")
        .group_by(CompanyProfile.name)
        .order_by(func.count(Evaluation.id).desc())
    )
    company_result = await db.execute(company_query)
    company_rows = company_result.all()

    def _round_or_none(val: any) -> float | None:
        return round(float(val), 1) if val else None

    company_breakdowns = [
        CompanyBreakdown(
            company_name=row[0],
            evaluation_count=row[1],
            average_score=_round_or_none(row[2]),
            best_score=_round_or_none(row[3]),
            situation_avg=_round_or_none(row[4]),
            task_avg=_round_or_none(row[5]),
            action_avg=_round_or_none(row[6]),
            result_avg=_round_or_none(row[7]),
            engagement_avg=_round_or_none(row[8]),
            overall_avg=_round_or_none(row[9]),
        )
        for row in company_rows
    ]

    # ── Readiness score ─────────────────────────────────────────────────
    readiness = None
    if total_count > 0:
        # Score component (40%): avg score on 1-5 scale → 0-100
        avg_scores = [
            float(dim_row[i]) for i in range(6) if dim_row[i] is not None
        ]
        overall_avg = sum(avg_scores) / len(avg_scores) if avg_scores else 0
        score_component = min(100, int((overall_avg / 5) * 100))

        # Consistency component (30%): low variance = high consistency
        if len(avg_scores) >= 2:
            mean_s = sum(avg_scores) / len(avg_scores)
            variance = sum((s - mean_s) ** 2 for s in avg_scores) / len(avg_scores)
            # Max variance on 1-5 scale is about 4.0; low variance → high score
            consistency_component = max(0, min(100, int((1 - (variance / 4)) * 100)))
        else:
            consistency_component = 50  # neutral if only one dimension

        # Trend component (30%): compare first and last evaluation averages
        trend_query = (
            select(Evaluation.average_score, Evaluation.created_at)
            .join(AnswerVersion, Evaluation.answer_version_id == AnswerVersion.id)
            .join(Answer, AnswerVersion.answer_id == Answer.id)
            .where(Answer.user_id == user.id, Evaluation.status == "completed")
            .order_by(Evaluation.created_at.asc())
        )
        trend_result = await db.execute(trend_query)
        trend_rows = trend_result.all()

        if len(trend_rows) >= 2:
            first_score = float(trend_rows[0][0]) if trend_rows[0][0] else 0
            last_score = float(trend_rows[-1][0]) if trend_rows[-1][0] else 0
            delta = last_score - first_score
            # Delta range: -4 to +4 on 1-5 scale; map to 0-100
            trend_component = max(0, min(100, int(50 + (delta / 4) * 50)))
        else:
            trend_component = 50  # neutral if only one evaluation

        # Weighted composite
        overall_readiness = int(
            score_component * 0.4
            + consistency_component * 0.3
            + trend_component * 0.3
        )

        # Label
        if overall_readiness >= 80:
            label = "Strong Candidate"
        elif overall_readiness >= 60:
            label = "Interview Ready"
        elif overall_readiness >= 40:
            label = "Getting There"
        else:
            label = "Not Ready"

        readiness = ReadinessScore(
            overall_readiness=overall_readiness,
            score_component=score_component,
            consistency_component=consistency_component,
            trend_component=trend_component,
            label=label,
        )

    return AnalyticsResponse(
        dimension_averages=dimension_averages,
        company_breakdowns=company_breakdowns,
        readiness=readiness,
    )
