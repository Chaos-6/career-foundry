"""
Scenario loader — reads agentic interview questions from scenarios.json.

Provides filtering by track, role, category, type, and difficulty.
Used by the question bank API and mock interview flow to serve
agentic questions alongside the existing DB-backed standard questions.

The scenarios file is loaded once at import time and cached in memory.
At 30 questions (~50KB), this is negligible.
"""

import json
import random
from pathlib import Path
from typing import Optional


_SCENARIOS_PATH = Path(__file__).parent.parent / "data" / "scenarios.json"

# Load once at import time
_ALL_SCENARIOS: list[dict] = []

if _SCENARIOS_PATH.exists():
    _ALL_SCENARIOS = json.loads(_SCENARIOS_PATH.read_text(encoding="utf-8"))


def get_scenarios(
    *,
    track: Optional[str] = None,
    role: Optional[str] = None,
    category: Optional[str] = None,
    interview_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> list[dict]:
    """Filter scenarios by any combination of fields.

    All filters are optional. Omitted filters match everything.

    Args:
        track: "agentic" or "standard".
        role: "AGENTIC_ENGINEER", "PM", "TPM", etc.
        category: "architecture_orchestration", "safety_alignment", etc.
        interview_type: "behavioral" or "system_design".
        difficulty: "hard", "expert", etc.
        tags: If provided, scenario must contain ALL specified tags.

    Returns:
        List of matching scenario dicts.
    """
    results = _ALL_SCENARIOS

    if track:
        results = [s for s in results if s.get("track") == track]
    if role:
        results = [s for s in results if s.get("role") == role]
    if category:
        results = [s for s in results if s.get("category") == category]
    if interview_type:
        results = [s for s in results if s.get("type") == interview_type]
    if difficulty:
        results = [s for s in results if s.get("difficulty") == difficulty]
    if tags:
        tag_set = set(tags)
        results = [s for s in results if tag_set.issubset(set(s.get("tags", [])))]

    return results


def get_random_scenario(
    *,
    track: Optional[str] = None,
    role: Optional[str] = None,
    category: Optional[str] = None,
    interview_type: Optional[str] = None,
    difficulty: Optional[str] = None,
) -> Optional[dict]:
    """Get a single random scenario matching the filters.

    Returns None if no scenarios match.
    """
    candidates = get_scenarios(
        track=track,
        role=role,
        category=category,
        interview_type=interview_type,
        difficulty=difficulty,
    )
    return random.choice(candidates) if candidates else None


def get_categories(track: str = "agentic") -> list[str]:
    """Get distinct category names for a track.

    Useful for populating filter dropdowns on the frontend.
    """
    return sorted(
        {s["category"] for s in _ALL_SCENARIOS if s.get("track") == track}
    )


def get_scenario_by_id(scenario_id: str) -> Optional[dict]:
    """Look up a scenario by its unique ID."""
    for s in _ALL_SCENARIOS:
        if s["id"] == scenario_id:
            return s
    return None
