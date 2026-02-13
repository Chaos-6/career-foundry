"""
Score extraction from Claude's evaluation markdown.

Parses the structured evaluation output to extract:
- 6 individual dimension scores (1-5)
- Average score
- Section boundaries for structured storage

The parser uses multiple regex patterns to handle format variations
in Claude's output. Scores are validated to ensure they're in the 1-5 range.
"""

import re
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class ParsedScores:
    """Extracted scores from an evaluation markdown."""

    situation_score: int | None = None
    task_score: int | None = None
    action_score: int | None = None
    result_score: int | None = None
    engagement_score: int | None = None
    overall_score: int | None = None
    average_score: Decimal | None = None

    @property
    def all_scores_present(self) -> bool:
        """Check if all 6 dimension scores were extracted."""
        return all(
            s is not None
            for s in [
                self.situation_score,
                self.task_score,
                self.action_score,
                self.result_score,
                self.engagement_score,
                self.overall_score,
            ]
        )

    def calculate_average(self) -> Decimal | None:
        """Calculate average from individual scores if all present."""
        if not self.all_scores_present:
            return None
        scores = [
            self.situation_score,
            self.task_score,
            self.action_score,
            self.result_score,
            self.engagement_score,
            self.overall_score,
        ]
        total = sum(scores)
        return Decimal(str(round(total / 6, 1)))


# ---------------------------------------------------------------------------
# Score extraction patterns
# ---------------------------------------------------------------------------

# Pattern 1: "1. Situation – Context & Stakes           [4/5]"
_BRACKET_PATTERN = re.compile(
    r"(\d+)\.\s*(Situation|Task|Action|Result|Engagement|Overall)"
    r".*?\[(\d)/5\]",
    re.IGNORECASE,
)

# Pattern 2: "Situation – Context & Stakes: 4/5"
_COLON_PATTERN = re.compile(
    r"(Situation|Task|Action|Result|Engagement|Overall)"
    r"[^:]*:\s*(\d)\s*/\s*5",
    re.IGNORECASE,
)

# Pattern 3: "**Situation:** 4/5" or "**Situation**: 4/5"
_BOLD_PATTERN = re.compile(
    r"\*\*(Situation|Task|Action|Result|Engagement|Overall)[^*]*\*\*:?\s*(\d)\s*/\s*5",
    re.IGNORECASE,
)

# Average pattern: "AVERAGE SCORE: [3.8/5]" or "AVERAGE SCORE: 3.8/5"
_AVERAGE_PATTERN = re.compile(
    r"AVERAGE\s*SCORE[:\s]*\[?(\d+\.?\d*)\s*/\s*5\]?",
    re.IGNORECASE,
)

# Dimension name → attribute mapping
_DIMENSION_MAP = {
    "situation": "situation_score",
    "task": "task_score",
    "action": "action_score",
    "result": "result_score",
    "engagement": "engagement_score",
    "overall": "overall_score",
}


def _validate_score(score: int) -> int | None:
    """Ensure score is in valid 1-5 range."""
    return score if 1 <= score <= 5 else None


def parse_scores(markdown: str) -> ParsedScores:
    """Extract dimension scores and average from evaluation markdown.

    Tries multiple regex patterns to handle Claude's format variations.
    Falls back to calculating average from individual scores if the
    explicit average isn't found.

    Args:
        markdown: The full evaluation markdown from Claude.

    Returns:
        ParsedScores with extracted values (None for any not found).
    """
    scores = ParsedScores()

    # Try each pattern in order of specificity
    for pattern in [_BRACKET_PATTERN, _COLON_PATTERN, _BOLD_PATTERN]:
        for match in pattern.finditer(markdown):
            # Different patterns have dimension name in different groups
            if pattern == _BRACKET_PATTERN:
                dimension = match.group(2).lower()
                score_val = int(match.group(3))
            else:
                dimension = match.group(1).lower()
                score_val = int(match.group(2))

            attr = _DIMENSION_MAP.get(dimension)
            if attr and getattr(scores, attr) is None:
                setattr(scores, attr, _validate_score(score_val))

    # Extract explicit average
    avg_match = _AVERAGE_PATTERN.search(markdown)
    if avg_match:
        avg_val = Decimal(avg_match.group(1))
        if Decimal("1") <= avg_val <= Decimal("5"):
            scores.average_score = avg_val

    # Fallback: calculate average if not found but all scores present
    if scores.average_score is None:
        scores.average_score = scores.calculate_average()

    return scores


@dataclass
class ParsedSections:
    """Extracted sections from the evaluation markdown."""

    scored_assessment: str = ""
    star_analysis: str = ""
    rewrite_suggestions: str = ""
    company_alignment: str = ""
    follow_up_questions: str = ""
    alternative_framing: str = ""
    length_timing: str = ""
    interview_ready: str = ""


# Section header patterns — match the evaluation prompt's section structure
_SECTION_PATTERNS = [
    ("scored_assessment", r"(?:###?\s*A\.|SCORED\s*ASSESSMENT|DIMENSION\s*SCORES)"),
    ("star_analysis", r"(?:###?\s*B\.|STAR-BY-STAR\s*ANALYSIS)"),
    ("rewrite_suggestions", r"(?:###?\s*C\.|REWRITE\s*SUGGESTIONS|GUIDING\s*QUESTIONS)"),
    ("company_alignment", r"(?:###?\s*D\.|COMPANY\s*CULTURE\s*ALIGNMENT|VALUES\s*FIT)"),
    ("follow_up_questions", r"(?:###?\s*E\.|FOLLOW-UP\s*QUESTIONS)"),
    ("alternative_framing", r"(?:###?\s*F\.|ALTERNATIVE\s*FRAMING)"),
    ("length_timing", r"(?:###?\s*G\.|LENGTH\s*&?\s*TIMING)"),
    ("interview_ready", r"(?:###?\s*H\.|INTERVIEW-READY\s*ASSESSMENT|FINAL\s*RECOMMENDATION)"),
]


def parse_sections(markdown: str) -> dict:
    """Extract evaluation sections from markdown for structured storage.

    Returns a dict suitable for storing in the evaluation_sections JSONB column.
    Each key maps to the text content of that section.
    """
    sections = {}

    # Find all section start positions
    positions = []
    for name, pattern in _SECTION_PATTERNS:
        match = re.search(pattern, markdown, re.IGNORECASE)
        if match:
            positions.append((match.start(), name))

    # Sort by position
    positions.sort(key=lambda x: x[0])

    # Extract text between section boundaries
    for i, (pos, name) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(markdown)
        section_text = markdown[pos:end].strip()
        sections[name] = section_text

    return sections


def parse_follow_up_questions(markdown: str) -> list[dict]:
    """Extract follow-up questions from the evaluation markdown.

    Returns list of dicts for the follow_up_questions JSONB column.
    """
    questions = []

    # Find the follow-up questions section
    section_match = re.search(
        r"(?:FOLLOW-UP\s*QUESTIONS|###?\s*E\.)(.*?)(?=###?\s*[F-Z]\.|$)",
        markdown,
        re.IGNORECASE | re.DOTALL,
    )
    if not section_match:
        return questions

    section_text = section_match.group(1)

    # Extract numbered questions
    q_pattern = re.compile(
        r'(\d+)\.\s*["\"]?(.*?)["\"]?\s*\n'
        r'(?:\s*[-*]\s*\*?Why.*?:\*?\s*(.*?)\n)?'
        r'(?:\s*[-*]\s*\*?How.*?:\*?\s*(.*?)(?:\n|$))?',
        re.IGNORECASE,
    )

    for match in q_pattern.finditer(section_text):
        q = {"question": match.group(2).strip().strip('"')}
        if match.group(3):
            q["why_asked"] = match.group(3).strip()
        if match.group(4):
            q["how_to_prepare"] = match.group(4).strip()
        if q["question"]:
            questions.append(q)

    return questions


def parse_company_alignment(markdown: str, company_name: str) -> dict:
    """Extract company alignment details from the evaluation markdown.

    Returns dict for the company_alignment JSONB column.
    """
    alignment = {
        "company": company_name,
        "aligned_principles": [],
        "reinforce_areas": [],
    }

    # Find the company alignment section
    section_match = re.search(
        r"(?:COMPANY\s*CULTURE\s*ALIGNMENT|VALUES\s*FIT|###?\s*D\.)(.*?)(?=###?\s*[E-Z]\.|$)",
        markdown,
        re.IGNORECASE | re.DOTALL,
    )
    if not section_match:
        return alignment

    section_text = section_match.group(1)

    # Look for "aligns" mentions
    align_matches = re.findall(
        r'["\"]?([\w\s&]+?)["\"]?\s*(?:through|via|by|with)',
        section_text,
        re.IGNORECASE,
    )
    if align_matches:
        alignment["aligned_principles"] = [m.strip() for m in align_matches[:5]]

    # Look for "reinforce" mentions
    reinforce_matches = re.findall(
        r'(?:reinforce|strengthen|emphasize)[^.]*?["\"]?([\w\s&]+?)["\"]',
        section_text,
        re.IGNORECASE,
    )
    if reinforce_matches:
        alignment["reinforce_areas"] = [m.strip() for m in reinforce_matches[:5]]

    return alignment
