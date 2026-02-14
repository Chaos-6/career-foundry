"""
Inline improvement suggestions service — targeted STAR section coaching.

Generates actionable improvement tips for specific STAR dimensions that scored
poorly (≤3). Uses Claude with a tight token budget (max_tokens=1000) since
we're generating focused suggestions, not full evaluations.

Design decisions:
- Separate from STARAnalysisService — different prompt, different token budget
- Synchronous Anthropic client (wrapped in asyncio.to_thread by the endpoint)
- Temperature 0.5 — slightly higher than evaluation (0.3) for more creative
  suggestions while still being grounded
- Returns structured JSON via Claude's tool_use for reliable parsing
"""

import json
import logging
from dataclasses import dataclass

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)


SUGGESTIONS_SYSTEM_PROMPT = """\
You are a behavioral interview coach specializing in STAR-format answers.

Given a completed evaluation with scores and the original answer, generate
targeted improvement suggestions ONLY for the weakest dimensions (those
scoring 3 or below out of 5).

For each weak dimension, provide:
1. A concise, actionable suggestion (2-3 sentences max)
2. A brief example showing what a strong version would look like (1-2 sentences)

Focus on the most impactful change the candidate can make. Be specific to
their actual answer — don't give generic advice.

Respond with a JSON array of suggestion objects. Each object must have:
- "section": the STAR dimension name (lowercase: "situation", "task", "action", "result", "engagement", "overall")
- "suggestion": actionable improvement tip (2-3 sentences)
- "example": a concrete example of how to improve that section (1-2 sentences)
"""


@dataclass
class SuggestionResult:
    """Result from the suggestions service."""

    suggestions: list[dict]  # [{section, suggestion, example}]
    input_tokens: int
    output_tokens: int


class SuggestionService:
    """Generates targeted improvement suggestions for weak STAR dimensions.

    Usage:
        service = SuggestionService()
        result = service.generate(
            answer_text="Situation: ...",
            scores={"situation": 2, "task": 4, ...},
            evaluation_markdown="...",
        )
    """

    MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 1000
    TEMPERATURE = 0.5

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate(
        self,
        *,
        answer_text: str,
        scores: dict[str, int | None],
        evaluation_markdown: str,
    ) -> SuggestionResult:
        """Generate improvement suggestions for weak dimensions.

        This is a synchronous call — the endpoint wraps it in
        asyncio.to_thread() to keep the event loop responsive.

        Args:
            answer_text: The original answer that was evaluated.
            scores: Dict of dimension name → score (1-5).
            evaluation_markdown: The full evaluation feedback text.

        Returns:
            SuggestionResult with structured suggestions and token counts.
        """
        # Filter to only weak dimensions (score ≤ 3)
        weak_dimensions = {
            dim: score
            for dim, score in scores.items()
            if score is not None and score <= 3
        }

        if not weak_dimensions:
            return SuggestionResult(suggestions=[], input_tokens=0, output_tokens=0)

        user_message = self._build_user_message(
            answer_text, weak_dimensions, evaluation_markdown
        )

        message = self.client.messages.create(
            model=self.MODEL,
            max_tokens=self.MAX_TOKENS,
            temperature=self.TEMPERATURE,
            system=SUGGESTIONS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        # Parse the JSON response
        raw_text = message.content[0].text
        suggestions = self._parse_suggestions(raw_text, weak_dimensions)

        return SuggestionResult(
            suggestions=suggestions,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )

    def _build_user_message(
        self,
        answer_text: str,
        weak_dimensions: dict[str, int],
        evaluation_markdown: str,
    ) -> str:
        """Build the user message with context for Claude."""
        weak_list = ", ".join(
            f"{dim} ({score}/5)" for dim, score in weak_dimensions.items()
        )

        return f"""\
## Original Answer
{answer_text}

## Weak Dimensions (need improvement)
{weak_list}

## Evaluation Feedback
{evaluation_markdown}

Generate targeted improvement suggestions ONLY for these weak dimensions: {', '.join(weak_dimensions.keys())}.
Respond with a JSON array — no markdown fences, just the raw JSON."""

    def _parse_suggestions(
        self, raw_text: str, weak_dimensions: dict[str, int]
    ) -> list[dict]:
        """Parse Claude's JSON response into structured suggestions.

        Falls back to a simple structure if parsing fails — we never want
        the endpoint to error just because Claude formatted oddly.
        """
        try:
            # Strip potential markdown code fences
            text = raw_text.strip()
            if text.startswith("```"):
                # Remove opening fence (with optional language tag)
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            suggestions = json.loads(text)

            # Validate structure
            if not isinstance(suggestions, list):
                raise ValueError("Expected a JSON array")

            # Filter to only dimensions we asked about
            valid = []
            for s in suggestions:
                if isinstance(s, dict) and s.get("section") in weak_dimensions:
                    valid.append({
                        "section": s["section"],
                        "suggestion": s.get("suggestion", ""),
                        "example": s.get("example", ""),
                    })

            return valid

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse suggestions JSON: %s", e)
            # Fallback: return the raw text as a single suggestion
            return [
                {
                    "section": list(weak_dimensions.keys())[0],
                    "suggestion": raw_text[:500],
                    "example": "",
                }
            ]
