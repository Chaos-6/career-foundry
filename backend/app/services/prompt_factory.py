"""
PromptFactory — Strategy Pattern for interview evaluation prompts.

Routes evaluation requests to the correct system prompt, user message format,
model parameters, and output parser based on the interview role and type.

Supported strategies:
  1. Standard STAR — markdown output, 6 dimensions (1-5 scale)
  2. Agentic Behavioral — JSON output, 4 dimensions (0-100 scale)
  3. Agentic System Design — JSON output, 4 dimensions (0-100 scale)

Usage:
    config = PromptFactory.create(
        role=InterviewRole.AGENTIC_ENGINEER,
        interview_type=InterviewType.BEHAVIORAL,
        question="Tell me about a time...",
        answer="I was working on...",
    )
    # config.system_message, config.user_message, config.temperature, etc.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class InterviewType(Enum):
    """The type of interview question being evaluated."""

    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system_design"


class InterviewRole(Enum):
    """The target role for the interview evaluation.

    Standard roles (PM, TPM, EM, MLE) use the existing STAR prompt.
    AGENTIC_ENGINEER uses specialized prompts with JSON output.
    """

    PM = "PM"
    TPM = "TPM"
    EM = "EM"
    MLE = "MLE"
    AGENTIC_ENGINEER = "AGENTIC"


@dataclass
class PromptConfig:
    """Everything the evaluation service needs to make a Claude call.

    Attributes:
        system_message: The system prompt defining the evaluator persona.
        user_message: The formatted user message with question + answer.
        temperature: Claude temperature parameter.
        max_tokens: Maximum output tokens.
        output_format: "markdown" or "json" — determines which parser to use.
        score_dimensions: Names of the scoring dimensions for this strategy.
    """

    system_message: str
    user_message: str
    temperature: float
    max_tokens: int
    output_format: str  # "markdown" or "json"
    score_dimensions: list[str]


class PromptFactory:
    """Routes interview evaluations to the correct prompt strategy."""

    @staticmethod
    def create(
        *,
        role: InterviewRole,
        interview_type: InterviewType,
        question: str,
        answer: str,
        # Standard STAR fields (only used for standard track)
        company_name: Optional[str] = None,
        principles: Optional[list[dict]] = None,
        principle_type: Optional[str] = None,
        interview_focus: Optional[str] = None,
        target_role: Optional[str] = None,
        experience_level: Optional[str] = None,
        word_count: Optional[int] = None,
    ) -> PromptConfig:
        """Build the prompt configuration for a given role + interview type.

        Args:
            role: The interview role (PM, MLE, AGENTIC_ENGINEER, etc.).
            interview_type: BEHAVIORAL or SYSTEM_DESIGN.
            question: The interview question text.
            answer: The candidate's response text.
            company_name..word_count: Additional context for standard STAR evaluations.

        Returns:
            PromptConfig with everything needed for the Claude API call.
        """
        if role == InterviewRole.AGENTIC_ENGINEER:
            if interview_type == InterviewType.SYSTEM_DESIGN:
                return _build_agentic_system_design(question, answer)
            else:
                return _build_agentic_behavioral(question, answer)
        else:
            return _build_standard_star(
                question=question,
                answer=answer,
                company_name=company_name or "General",
                principles=principles or [],
                principle_type=principle_type or "Values",
                interview_focus=interview_focus or "",
                target_role=target_role or role.value,
                experience_level=experience_level or "senior",
                word_count=word_count,
            )


# ---------------------------------------------------------------------------
# Strategy builders (private)
# ---------------------------------------------------------------------------


def _build_agentic_behavioral(question: str, answer: str) -> PromptConfig:
    """Agentic Engineer — Behavioral interview prompt (JSON output)."""
    from app.services.prompts_agentic import AGENTIC_BEHAVIORAL_PROMPT

    user_message = f"Question: {question}\nResponse: {answer}"

    return PromptConfig(
        system_message=AGENTIC_BEHAVIORAL_PROMPT,
        user_message=user_message,
        temperature=0.3,
        max_tokens=4000,
        output_format="json",
        score_dimensions=[
            "agentic_thinking",
            "safety_alignment",
            "engineering_rigor",
            "communication",
        ],
    )


def _build_agentic_system_design(question: str, answer: str) -> PromptConfig:
    """Agentic Engineer — System Design interview prompt (JSON output)."""
    from app.services.prompts_agentic import AGENTIC_SYSTEM_DESIGN_PROMPT

    user_message = f"Design Question: {question}\nCandidate Design: {answer}"

    return PromptConfig(
        system_message=AGENTIC_SYSTEM_DESIGN_PROMPT,
        user_message=user_message,
        temperature=0.2,
        max_tokens=4000,
        output_format="json",
        score_dimensions=[
            "requirements_clarity",
            "architecture_soundness",
            "agentic_patterns",
            "safety_security",
        ],
    )


def _build_standard_star(
    *,
    question: str,
    answer: str,
    company_name: str,
    principles: list[dict],
    principle_type: str,
    interview_focus: str,
    target_role: str,
    experience_level: str,
    word_count: int | None,
) -> PromptConfig:
    """Standard STAR evaluation — markdown output, 6 dimensions."""
    from app.services.prompts import SYSTEM_PROMPT, build_evaluation_user_message

    user_message = build_evaluation_user_message(
        question_text=question,
        answer_text=answer,
        company_name=company_name,
        principles=principles,
        principle_type=principle_type,
        interview_focus=interview_focus,
        target_role=target_role,
        experience_level=experience_level,
        word_count=word_count,
    )

    return PromptConfig(
        system_message=SYSTEM_PROMPT,
        user_message=user_message,
        temperature=0.3,
        max_tokens=8000,
        output_format="markdown",
        score_dimensions=[
            "situation",
            "task",
            "action",
            "result",
            "engagement",
            "overall",
        ],
    )
