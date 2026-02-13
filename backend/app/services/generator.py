"""
AI Answer Generator service.

Takes bullet-point inputs from the user and generates a STAR-formatted
narrative answer using Claude. This is a separate concern from evaluation —
it uses a different system prompt, higher temperature, and constructs
a narrative rather than scoring one.

Design decisions:
- Temperature 0.5 (more creative than evaluation's 0.3)
- Max 2000 tokens (shorter output — just the answer)
- Separate system prompt focused on narrative construction
"""

import time
from dataclasses import dataclass

import anthropic

from app.config import settings


GENERATOR_SYSTEM_PROMPT = """You are an expert career coach helping candidates write STAR-formatted behavioral interview answers.

Given a behavioral question, target company/role, and bullet-point inputs for each STAR component, generate a polished, interview-ready narrative answer.

Guidelines:
- Write in first person as if the candidate is speaking
- Keep the total answer between 200-400 words (2-3 minutes when spoken)
- Situation: 2-3 sentences establishing context and stakes
- Task: 1-2 sentences clarifying personal responsibility
- Action: 3-5 sentences with clear reasoning and trade-offs
- Result: 2-3 sentences with quantified outcomes and learning
- Use natural, conversational language — not robotic or rehearsed
- Include specific details from the bullet points
- Weave in alignment with the target company's values where natural
- Do NOT add fictional details — only elaborate on what's provided

Output just the STAR answer text, nothing else. No headers, no labels."""


@dataclass
class GeneratorResult:
    """Result from the answer generation."""

    answer_text: str
    model: str
    input_tokens: int
    output_tokens: int
    processing_seconds: int


class AnswerGeneratorService:
    """Generates STAR-formatted answers from bullet-point inputs."""

    MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 2000
    TEMPERATURE = 0.5

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate(
        self,
        *,
        question_text: str,
        company_name: str,
        target_role: str,
        experience_level: str,
        situation_bullets: str,
        task_bullets: str,
        action_bullets: str,
        result_bullets: str,
    ) -> GeneratorResult:
        """Generate a STAR answer from bullet-point inputs.

        Synchronous — the router wraps this in asyncio.to_thread().
        """
        user_message = f"""## Context
**Company:** {company_name}
**Role:** {target_role}
**Level:** {experience_level}

## Question
{question_text}

## Bullet-Point Inputs

**SITUATION:**
{situation_bullets}

**TASK:**
{task_bullets}

**ACTION:**
{action_bullets}

**RESULT:**
{result_bullets}

Please generate a polished, interview-ready STAR answer from these inputs."""

        start = time.time()

        message = self.client.messages.create(
            model=self.MODEL,
            max_tokens=self.MAX_TOKENS,
            temperature=self.TEMPERATURE,
            system=GENERATOR_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        elapsed = int(time.time() - start)

        return GeneratorResult(
            answer_text=message.content[0].text,
            model=self.MODEL,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            processing_seconds=elapsed,
        )
