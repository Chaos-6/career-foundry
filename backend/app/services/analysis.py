"""
STAR Analysis Service — Claude API integration.

Thin wrapper around the Anthropic SDK. Sends the evaluation system prompt
+ user context to Claude and returns the raw markdown response with token
accounting.

Design decisions:
- Synchronous Anthropic client (wrapped in asyncio.to_thread by the pipeline)
- Temperature 0.3 for consistent, reproducible evaluations
- claude-sonnet-4-20250514 for quality/cost balance
- Max 8000 tokens to accommodate the full 8-section evaluation structure
"""

import time
from dataclasses import dataclass

import anthropic

from app.config import settings
from app.services.prompts import SYSTEM_PROMPT, build_evaluation_user_message


@dataclass
class EvaluationResult:
    """Raw result from Claude's evaluation."""

    markdown: str
    model: str
    input_tokens: int
    output_tokens: int
    processing_seconds: int


class STARAnalysisService:
    """Evaluates behavioral interview answers using Claude.

    Usage:
        service = STARAnalysisService()
        result = service.evaluate(
            question_text="Tell me about a time...",
            answer_text="Situation: ...",
            company_name="Amazon",
            ...
        )
    """

    MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 8000
    TEMPERATURE = 0.3

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def evaluate(
        self,
        *,
        question_text: str,
        answer_text: str,
        company_name: str,
        principles: list[dict],
        principle_type: str,
        interview_focus: str,
        target_role: str,
        experience_level: str,
        word_count: int | None = None,
    ) -> EvaluationResult:
        """Run a STAR evaluation against Claude.

        This is a synchronous call — the pipeline wraps it in
        asyncio.to_thread() to keep the event loop responsive.

        Args:
            question_text: The behavioral question being answered.
            answer_text: The candidate's STAR-formatted answer.
            company_name: Target company (e.g., "Amazon").
            principles: Company principles as [{name, description}].
            principle_type: e.g., "Leadership Principles", "Core Values".
            interview_focus: Company-specific interview guidance.
            target_role: e.g., "MLE", "PM", "EM".
            experience_level: e.g., "senior", "staff", "entry".
            word_count: Optional word count of the answer.

        Returns:
            EvaluationResult with markdown, token counts, and timing.
        """
        user_message = build_evaluation_user_message(
            question_text=question_text,
            answer_text=answer_text,
            company_name=company_name,
            principles=principles,
            principle_type=principle_type,
            interview_focus=interview_focus,
            target_role=target_role,
            experience_level=experience_level,
            word_count=word_count,
        )

        start = time.time()

        message = self.client.messages.create(
            model=self.MODEL,
            max_tokens=self.MAX_TOKENS,
            temperature=self.TEMPERATURE,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        elapsed = int(time.time() - start)

        return EvaluationResult(
            markdown=message.content[0].text,
            model=self.MODEL,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            processing_seconds=elapsed,
        )
