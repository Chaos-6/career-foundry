"""
Prompt management for the STAR evaluation engine.

Loads the evaluation system prompt from disk once at module level.
Builds user messages by injecting company context, candidate metadata,
and the answer text.

Architecture:
- System message = evaluation framework (STAR-eval-prompt_v1.md)
- User message = specific context to evaluate (company + role + question + answer)

This separation means the system prompt stays constant across evaluations,
and token caching can kick in for repeated calls.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Load system prompt once at import time
# ---------------------------------------------------------------------------

# In production: prompt file lives alongside the project
# Fall back to the Components directory during development
_PROMPT_PATHS = [
    Path(__file__).parent.parent.parent / "prompts" / "STAR-eval-prompt_v1.md",
    Path("/Users/davidreed/behavioral/Components/STAR-eval-prompt_v1.md"),
]

SYSTEM_PROMPT: str = ""

for path in _PROMPT_PATHS:
    if path.exists():
        SYSTEM_PROMPT = path.read_text(encoding="utf-8")
        break

if not SYSTEM_PROMPT:
    raise RuntimeError(
        "Could not find STAR-eval-prompt_v1.md. "
        f"Searched: {[str(p) for p in _PROMPT_PATHS]}"
    )


# ---------------------------------------------------------------------------
# User message builder
# ---------------------------------------------------------------------------

def build_evaluation_user_message(
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
) -> str:
    """Build the user message that provides evaluation context.

    The system prompt contains the evaluation framework. This function
    builds the per-evaluation context: who the candidate is, what company
    they're targeting, and the actual answer to evaluate.
    """
    # Format principles as readable list
    principles_text = "\n".join(
        f"  - **{p['name']}**: {p.get('description', '')}"
        for p in principles
    )

    word_info = f"\n**Word Count:** {word_count}" if word_count else ""

    return f"""## EVALUATION CONTEXT

**Target Company:** {company_name}
**Target Role:** {target_role}
**Experience Level:** {experience_level}

### {company_name} — {principle_type}

{principles_text}

**Interview Focus:** {interview_focus}

---

## BEHAVIORAL QUESTION

{question_text}

---

## CANDIDATE'S ANSWER
{word_info}

{answer_text}

---

Please evaluate this answer using the full evaluation framework. Provide:
1. Scored assessment across all 6 dimensions (1-5 each)
2. STAR-by-STAR analysis with strengths and opportunities
3. Specific rewrite suggestions and guiding questions
4. Company culture alignment analysis for {company_name}
5. Follow-up questions to expect
6. Alternative framing suggestions
7. Length & timing feedback
8. Interview-ready assessment with top 3 priorities
"""
