"""
Bulk import parser — extracts STAR answers from .txt and .md files.

Parses uploaded files that contain one or more STAR-formatted answers,
each optionally preceded by a question header. Supports two formats:

Format 1 — Multiple answers separated by "---" or "===":
    ## Question: Tell me about a time...
    Situation: ...
    Task: ...
    Action: ...
    Result: ...
    ---
    ## Question: Describe a situation where...
    Situation: ...

Format 2 — Single answer with STAR headers:
    Situation: At my previous company...
    Task: I needed to...
    Action: I decided to...
    Result: As a result...

Design decisions:
- Regex-based parsing for flexibility (handles ## headers, bold, plain text)
- Minimum 10 words per answer (matches AnswerCreateRequest validation)
- Max 100KB file size enforced at the endpoint, not here
- Returns structured results with per-answer validation errors
"""

import re
from dataclasses import dataclass, field


@dataclass
class ParsedAnswer:
    """A single parsed answer from a bulk import file."""

    question_text: str | None  # Extracted question, if present
    answer_text: str           # Full answer text (concatenated STAR sections)
    word_count: int
    line_number: int           # Approximate line in source file


@dataclass
class ImportParseResult:
    """Result of parsing an import file."""

    answers: list[ParsedAnswer] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    total_found: int = 0


# Regex patterns for STAR section headers
QUESTION_PATTERN = re.compile(
    r"^(?:#{1,3}\s*)?(?:question|q)\s*[:：]\s*(.+)",
    re.IGNORECASE | re.MULTILINE,
)

# Separator between answers
ANSWER_SEPARATOR = re.compile(r"^[-=]{3,}\s*$", re.MULTILINE)

# Minimum word count for a valid answer
MIN_WORDS = 10


def parse_import_file(content: str) -> ImportParseResult:
    """Parse an uploaded text file into individual STAR answers.

    Args:
        content: Raw file content as a string.

    Returns:
        ImportParseResult with parsed answers and any validation errors.
    """
    result = ImportParseResult()

    if not content.strip():
        result.errors.append("File is empty.")
        return result

    # Split into answer blocks by separator
    blocks = ANSWER_SEPARATOR.split(content)

    # Filter out empty blocks
    blocks = [b.strip() for b in blocks if b.strip()]

    if not blocks:
        result.errors.append("No answers found in the file.")
        return result

    result.total_found = len(blocks)

    for i, block in enumerate(blocks):
        parsed = _parse_answer_block(block, i + 1)
        if parsed:
            result.answers.append(parsed)
        else:
            result.errors.append(
                f"Block {i + 1}: Answer too short (needs at least {MIN_WORDS} words)."
            )

    return result


def _parse_answer_block(block: str, block_number: int) -> ParsedAnswer | None:
    """Parse a single answer block, extracting question and answer text.

    Returns None if the block doesn't contain enough content.
    """
    lines = block.split("\n")

    # Try to extract a question from the first line(s)
    question_text = None
    answer_start = 0

    match = QUESTION_PATTERN.match(lines[0])
    if match:
        question_text = match.group(1).strip()
        answer_start = 1

    # The rest is the answer text
    answer_lines = lines[answer_start:]
    answer_text = "\n".join(answer_lines).strip()

    if not answer_text:
        return None

    word_count = len(answer_text.split())
    if word_count < MIN_WORDS:
        return None

    # Approximate line number for error reporting
    line_number = sum(len(block.split("\n")) for block in []) + 1

    return ParsedAnswer(
        question_text=question_text,
        answer_text=answer_text,
        word_count=word_count,
        line_number=block_number,
    )
