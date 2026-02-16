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

Supports two evaluation tracks:
1. Standard STAR — markdown output, regex-parsed scores (1-5)
2. Agentic — JSON output, directly parsed scores (0-100)

The track is determined by the Answer's track field. The PromptFactory
selects the correct prompt, parameters, and parser.
"""

import asyncio
import json
import logging
import time
from decimal import Decimal
from typing import Optional
from uuid import UUID

import anthropic

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import Answer, AnswerVersion, CompanyProfile, Evaluation, User
from app.services.prompt_factory import (
    InterviewRole,
    InterviewType,
    PromptConfig,
    PromptFactory,
)
from app.services.score_parser import (
    parse_company_alignment,
    parse_follow_up_questions,
    parse_scores,
    parse_sections,
)

logger = logging.getLogger(__name__)


async def run_evaluation_pipeline(
    evaluation_id: UUID,
    user_id: Optional[UUID] = None,
) -> None:
    """Run the full evaluation pipeline for an evaluation record.

    Manages its own AsyncSession since this runs outside the request
    lifecycle (as a BackgroundTask). Commits after each stage transition
    so the frontend can poll status.

    Args:
        evaluation_id: UUID of the Evaluation record to process.
        user_id: Optional UUID of the user — used to increment their
                 monthly evaluation counter on success.
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

            # Load answer (with company relationship — nullable for agentic)
            answer_result = await db.execute(
                select(Answer)
                .where(Answer.id == version.answer_id)
                .options(selectinload(Answer.company))
            )
            answer = answer_result.scalar_one_or_none()

            if not answer:
                await _fail_evaluation(db, evaluation, "Answer not found")
                return

            # Standard track requires a company; agentic does not
            is_agentic = answer.track == "agentic"
            company = answer.company

            if not is_agentic and not company:
                await _fail_evaluation(db, evaluation, "Company not found for standard evaluation")
                return

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
            # 3. Build prompt config via PromptFactory
            # ----------------------------------------------------------
            role = _resolve_role(answer.target_role, is_agentic)
            interview_type = _resolve_interview_type(answer.interview_type)

            prompt_config = PromptFactory.create(
                role=role,
                interview_type=interview_type,
                question=question_text,
                answer=version.answer_text,
                company_name=company.name if company else None,
                principles=company.principles if company else None,
                principle_type=company.principle_type if company else None,
                interview_focus=company.interview_focus if company else None,
                target_role=answer.target_role,
                experience_level=answer.experience_level,
                word_count=version.word_count,
            )

            # ----------------------------------------------------------
            # 4. Call Claude
            # ----------------------------------------------------------
            result = await asyncio.to_thread(
                _call_claude, prompt_config
            )

            # ----------------------------------------------------------
            # 5. Parse and store results based on track
            # ----------------------------------------------------------
            evaluation.model_used = result["model"]
            evaluation.input_tokens = result["input_tokens"]
            evaluation.output_tokens = result["output_tokens"]
            evaluation.processing_seconds = result["processing_seconds"]

            if is_agentic:
                _store_agentic_results(evaluation, result["content"])
            else:
                _store_standard_results(
                    evaluation, result["content"],
                    company.name if company else "General",
                )

            evaluation.status = "completed"
            await db.commit()

            # ----------------------------------------------------------
            # 6. Update answer's best score if this is better
            # ----------------------------------------------------------
            avg = _get_average_score(evaluation)
            if avg is not None:
                if answer.best_average_score is None or avg > answer.best_average_score:
                    answer.best_average_score = avg
                    await db.commit()

            # ----------------------------------------------------------
            # 7. Increment user's monthly counter, streak, and badges
            # ----------------------------------------------------------
            if user_id:
                user_result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = user_result.scalar_one_or_none()
                if user:
                    user.evaluations_this_month = (user.evaluations_this_month or 0) + 1

                    # Update practice streak and check badges
                    try:
                        from app.services.gamification import update_streak, check_and_award_badges
                        update_streak(user)
                        await check_and_award_badges(user, evaluation, db)
                    except Exception:
                        logger.exception("Gamification update failed (non-fatal)")

                    await db.commit()

            logger.info(
                f"Evaluation {evaluation_id} completed: "
                f"type={evaluation.evaluation_type}, "
                f"tokens={result['input_tokens']}+{result['output_tokens']}, "
                f"time={result['processing_seconds']}s"
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


# ---------------------------------------------------------------------------
# Claude API call
# ---------------------------------------------------------------------------


def _call_claude(config: PromptConfig) -> dict:
    """Make a synchronous Claude API call using the prompt config.

    Wrapped in asyncio.to_thread() by the pipeline.
    """
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    start = time.time()

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        system=config.system_message,
        messages=[{"role": "user", "content": config.user_message}],
    )

    elapsed = int(time.time() - start)

    return {
        "content": message.content[0].text,
        "model": "claude-sonnet-4-20250514",
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
        "processing_seconds": elapsed,
    }


# ---------------------------------------------------------------------------
# Result storage — standard vs agentic
# ---------------------------------------------------------------------------


def _store_standard_results(
    evaluation: Evaluation,
    markdown: str,
    company_name: str,
) -> None:
    """Parse and store standard STAR evaluation results."""
    evaluation.evaluation_type = "standard"
    evaluation.evaluation_markdown = markdown

    scores = parse_scores(markdown)
    sections = parse_sections(markdown)
    follow_ups = parse_follow_up_questions(markdown)
    alignment = parse_company_alignment(markdown, company_name)

    evaluation.situation_score = scores.situation_score
    evaluation.task_score = scores.task_score
    evaluation.action_score = scores.action_score
    evaluation.result_score = scores.result_score
    evaluation.engagement_score = scores.engagement_score
    evaluation.overall_score = scores.overall_score
    evaluation.average_score = scores.average_score

    evaluation.evaluation_sections = sections
    evaluation.follow_up_questions = follow_ups
    evaluation.company_alignment = alignment


def _store_agentic_results(evaluation: Evaluation, content: str) -> None:
    """Parse and store agentic evaluation results (JSON)."""
    evaluation.evaluation_type = "agentic"

    # Claude should return pure JSON, but handle markdown fences gracefully
    cleaned = content.strip()
    if cleaned.startswith("```"):
        # Strip ```json ... ``` fences
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse agentic JSON: {e}\nContent: {content[:500]}")
        raise ValueError(f"Claude returned invalid JSON for agentic evaluation: {e}")

    # Store the full structured result
    evaluation.agentic_result = result
    evaluation.agentic_scores = result.get("scores", {})
    evaluation.hiring_decision = result.get("hiring_decision")

    # Calculate average for best_score tracking (normalize 0-100 to Decimal)
    scores = result.get("scores", {})
    if scores:
        avg = sum(scores.values()) / len(scores)
        # Store as 0-100 scale in average_score (Numeric(2,1) won't fit —
        # we use agentic_scores for display, but set average_score to
        # the 1-5 equivalent for compatibility with existing best_average_score)
        evaluation.average_score = Decimal(str(round(avg / 20, 1)))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_role(target_role: str, is_agentic: bool) -> InterviewRole:
    """Map the answer's target_role string to an InterviewRole enum."""
    if is_agentic:
        return InterviewRole.AGENTIC_ENGINEER

    role_map = {
        "PM": InterviewRole.PM,
        "TPM": InterviewRole.TPM,
        "EM": InterviewRole.EM,
        "MLE": InterviewRole.MLE,
    }
    return role_map.get(target_role, InterviewRole.MLE)


def _resolve_interview_type(interview_type: str) -> InterviewType:
    """Map the answer's interview_type string to an InterviewType enum."""
    if interview_type == "system_design":
        return InterviewType.SYSTEM_DESIGN
    return InterviewType.BEHAVIORAL


def _get_average_score(evaluation: Evaluation) -> Optional[Decimal]:
    """Get the average score for an evaluation, regardless of type."""
    return evaluation.average_score


async def _fail_evaluation(db, evaluation: Evaluation, error_message: str) -> None:
    """Mark an evaluation as failed with an error message."""
    evaluation.status = "failed"
    evaluation.error_message = error_message
    await db.commit()
    logger.error(f"Evaluation {evaluation.id} failed: {error_message}")
