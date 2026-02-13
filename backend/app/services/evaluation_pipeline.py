"""
Evaluation pipeline — orchestrates the full answer evaluation flow.

This runs as a FastAPI BackgroundTask after the evaluation record is created.
It manages its own DB session (since background tasks run outside request
lifecycle) and commits at each status transition so the frontend can poll
progress.

Pipeline stages:
    queued → analyzing → completed
                ↓ (on error)
              failed

Unlike ALCA's pipeline which has transcription + analysis + report stages,
BIAE's pipeline is simpler: one Claude call, one parse, done.
"""

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models import Answer, AnswerVersion, CompanyProfile, Evaluation
from app.services.analysis import STARAnalysisService
from app.services.score_parser import (
    parse_company_alignment,
    parse_follow_up_questions,
    parse_scores,
    parse_sections,
)

logger = logging.getLogger(__name__)


async def run_evaluation_pipeline(evaluation_id: UUID) -> None:
    """Run the full evaluation pipeline for an evaluation record.

    Manages its own AsyncSession since this runs outside the request
    lifecycle (as a BackgroundTask). Commits after each stage transition
    so the frontend can poll status.

    Args:
        evaluation_id: UUID of the Evaluation record to process.
    """
    async with AsyncSessionLocal() as db:
        try:
            # ----------------------------------------------------------
            # 1. Load evaluation + related records
            # ----------------------------------------------------------
            eval_result = await db.execute(
                select(Evaluation).where(Evaluation.id == evaluation_id)
            )
            evaluation = eval_result.scalar_one_or_none()

            if not evaluation:
                logger.error(f"Evaluation {evaluation_id} not found")
                return

            # Load answer version
            version_result = await db.execute(
                select(AnswerVersion).where(
                    AnswerVersion.id == evaluation.answer_version_id
                )
            )
            version = version_result.scalar_one_or_none()

            if not version:
                await _fail_evaluation(db, evaluation, "Answer version not found")
                return

            # Load answer (with company relationship)
            answer_result = await db.execute(
                select(Answer)
                .where(Answer.id == version.answer_id)
                .options(selectinload(Answer.company))
            )
            answer = answer_result.scalar_one_or_none()

            if not answer or not answer.company:
                await _fail_evaluation(db, evaluation, "Answer or company not found")
                return

            company = answer.company

            # Get question text (from linked question or custom)
            question_text = answer.custom_question_text
            if answer.question_id and not question_text:
                from app.models import Question

                q_result = await db.execute(
                    select(Question).where(Question.id == answer.question_id)
                )
                question = q_result.scalar_one_or_none()
                question_text = question.question_text if question else "General behavioral question"

            if not question_text:
                question_text = "General behavioral question"

            # ----------------------------------------------------------
            # 2. Update status: analyzing
            # ----------------------------------------------------------
            evaluation.status = "analyzing"
            await db.commit()

            # ----------------------------------------------------------
            # 3. Call Claude via STARAnalysisService
            # ----------------------------------------------------------
            service = STARAnalysisService()

            result = await asyncio.to_thread(
                service.evaluate,
                question_text=question_text,
                answer_text=version.answer_text,
                company_name=company.name,
                principles=company.principles or [],
                principle_type=company.principle_type,
                interview_focus=company.interview_focus or "",
                target_role=answer.target_role,
                experience_level=answer.experience_level,
                word_count=version.word_count,
            )

            # ----------------------------------------------------------
            # 4. Parse scores and sections from Claude's response
            # ----------------------------------------------------------
            scores = parse_scores(result.markdown)
            sections = parse_sections(result.markdown)
            follow_ups = parse_follow_up_questions(result.markdown)
            alignment = parse_company_alignment(result.markdown, company.name)

            # ----------------------------------------------------------
            # 5. Store results
            # ----------------------------------------------------------
            evaluation.status = "completed"
            evaluation.evaluation_markdown = result.markdown

            # Individual scores
            evaluation.situation_score = scores.situation_score
            evaluation.task_score = scores.task_score
            evaluation.action_score = scores.action_score
            evaluation.result_score = scores.result_score
            evaluation.engagement_score = scores.engagement_score
            evaluation.overall_score = scores.overall_score
            evaluation.average_score = scores.average_score

            # Structured data
            evaluation.evaluation_sections = sections
            evaluation.follow_up_questions = follow_ups
            evaluation.company_alignment = alignment

            # API metadata
            evaluation.model_used = result.model
            evaluation.input_tokens = result.input_tokens
            evaluation.output_tokens = result.output_tokens
            evaluation.processing_seconds = result.processing_seconds

            await db.commit()

            # ----------------------------------------------------------
            # 6. Update answer's best score if this is better
            # ----------------------------------------------------------
            if scores.average_score is not None:
                if (
                    answer.best_average_score is None
                    or scores.average_score > answer.best_average_score
                ):
                    answer.best_average_score = scores.average_score
                    await db.commit()

            logger.info(
                f"Evaluation {evaluation_id} completed: "
                f"avg={scores.average_score}, "
                f"tokens={result.input_tokens}+{result.output_tokens}, "
                f"time={result.processing_seconds}s"
            )

        except Exception as e:
            logger.exception(f"Evaluation pipeline failed for {evaluation_id}")
            # Try to mark as failed — use a fresh query to avoid stale state
            try:
                eval_result = await db.execute(
                    select(Evaluation).where(Evaluation.id == evaluation_id)
                )
                evaluation = eval_result.scalar_one_or_none()
                if evaluation:
                    await _fail_evaluation(db, evaluation, str(e))
            except Exception:
                logger.exception("Failed to mark evaluation as failed")


async def _fail_evaluation(db, evaluation: Evaluation, error_message: str) -> None:
    """Mark an evaluation as failed with an error message."""
    evaluation.status = "failed"
    evaluation.error_message = error_message
    await db.commit()
    logger.error(f"Evaluation {evaluation.id} failed: {error_message}")
