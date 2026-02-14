"""
Evaluation endpoints.

POST creates an evaluation record and kicks off the Claude analysis
as a background task. GET polls the evaluation status/results.

The evaluation pipeline runs asynchronously — the frontend polls
GET /evaluations/{id} until status transitions to 'completed' or 'failed'.

Tier enforcement:
  Free users get FREE_EVALUATIONS_PER_MONTH evaluations/month.
  Pro users get PRO_EVALUATIONS_PER_MONTH (effectively unlimited).
  Anonymous users (no auth) are not allowed to create evaluations.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Answer, AnswerVersion, CompanyProfile, Evaluation, Question, User
from app.schemas.evaluations import EvaluationCreateRequest, EvaluationResponse
from app.services.evaluation_pipeline import run_evaluation_pipeline
from app.rate_limit import rate_limit
from app.services.pdf_report import PDFReportGenerator

router = APIRouter(prefix="/api/v1/evaluations", tags=["evaluations"])


# 10 evaluations per minute — each one triggers a Claude API call
@router.post(
    "",
    response_model=EvaluationResponse,
    status_code=201,
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))],
)
async def create_evaluation(
    request: EvaluationCreateRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new evaluation and kick off the analysis pipeline.

    Requires authentication. Checks the user's tier before allowing
    the evaluation — free users have a monthly limit, pro users don't.

    The evaluation is created with status='queued', then the background
    task runs the Claude analysis. The frontend polls GET /evaluations/{id}
    to track progress.

    Returns the evaluation immediately (status=queued) — don't wait
    for Claude.
    """
    # --- Tier enforcement ---
    tier_limit = (
        settings.PRO_EVALUATIONS_PER_MONTH
        if user.plan_tier == "pro"
        else settings.FREE_EVALUATIONS_PER_MONTH
    )
    if user.evaluations_this_month >= tier_limit:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "TIER_LIMIT_REACHED",
                "message": (
                    f"You've used all {tier_limit} evaluations this month. "
                    f"{'Upgrade to Pro for unlimited evaluations.' if user.plan_tier == 'free' else 'Contact support if you need more.'}"
                ),
                "current_usage": user.evaluations_this_month,
                "limit": tier_limit,
                "plan_tier": user.plan_tier,
            },
        )

    # Validate answer version exists
    version_result = await db.execute(
        select(AnswerVersion).where(AnswerVersion.id == request.answer_version_id)
    )
    version = version_result.scalar_one_or_none()

    if not version:
        raise HTTPException(status_code=404, detail="Answer version not found")

    # Create evaluation record
    evaluation = Evaluation(
        answer_version_id=request.answer_version_id,
        status="queued",
    )
    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)

    # Kick off background pipeline (passes user_id for counter increment)
    background_tasks.add_task(run_evaluation_pipeline, evaluation.id, user.id)

    return EvaluationResponse.model_validate(evaluation)


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation(
    evaluation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get evaluation status and results.

    The frontend polls this endpoint with refetchInterval until
    status is 'completed' or 'failed'.

    Status transitions:
        queued → analyzing → completed
                          → failed (with error_message)
    """
    result = await db.execute(
        select(Evaluation).where(Evaluation.id == evaluation_id)
    )
    evaluation = result.scalar_one_or_none()

    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    # Enrich with answer version data for the revision flow.
    # The frontend needs answer_id (to POST new versions) and answer_text
    # (to pre-populate the revision editor).
    response = EvaluationResponse.model_validate(evaluation)
    version_result = await db.execute(
        select(AnswerVersion).where(AnswerVersion.id == evaluation.answer_version_id)
    )
    version = version_result.scalar_one_or_none()
    if version:
        response.answer_id = version.answer_id
        response.answer_text = version.answer_text
        response.version_number = version.version_number

    return response


@router.get("/{evaluation_id}/report/pdf")
async def download_evaluation_pdf(
    evaluation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Download the evaluation as a professional PDF report.

    Only available for completed evaluations. Generates the PDF on-demand
    (fast enough that no caching is needed for MVP).
    """
    # Load evaluation
    result = await db.execute(
        select(Evaluation).where(Evaluation.id == evaluation_id)
    )
    evaluation = result.scalar_one_or_none()

    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    if evaluation.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Evaluation is not complete (status: {evaluation.status})",
        )

    # Load answer version → answer → company + question
    version_result = await db.execute(
        select(AnswerVersion).where(AnswerVersion.id == evaluation.answer_version_id)
    )
    version = version_result.scalar_one_or_none()

    answer_result = await db.execute(
        select(Answer)
        .where(Answer.id == version.answer_id)
        .options(selectinload(Answer.company))
    )
    answer = answer_result.scalar_one_or_none()
    company = answer.company

    # Get question text
    question_text = answer.custom_question_text
    if answer.question_id and not question_text:
        q_result = await db.execute(
            select(Question).where(Question.id == answer.question_id)
        )
        question = q_result.scalar_one_or_none()
        question_text = question.question_text if question else "General behavioral question"
    if not question_text:
        question_text = "General behavioral question"

    # Generate PDF
    generator = PDFReportGenerator()
    pdf_bytes = generator.generate_evaluation_report(
        company_name=company.name,
        target_role=answer.target_role,
        experience_level=answer.experience_level,
        question_text=question_text,
        answer_text=version.answer_text,
        word_count=version.word_count,
        situation_score=evaluation.situation_score,
        task_score=evaluation.task_score,
        action_score=evaluation.action_score,
        result_score=evaluation.result_score,
        engagement_score=evaluation.engagement_score,
        overall_score=evaluation.overall_score,
        average_score=evaluation.average_score,
        evaluation_markdown=evaluation.evaluation_markdown,
        company_alignment=evaluation.company_alignment,
        follow_up_questions=evaluation.follow_up_questions,
        evaluation_sections=evaluation.evaluation_sections,
    )

    filename = f"STAR_Evaluation_{company.slug}_{answer.target_role}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
