"""
Agentic scenarios endpoints.

Serves questions from the file-backed scenarios.json for the agentic track.
These are curated questions that ship with the app, separate from the
DB-backed question bank.

Public endpoints (no auth):
  GET /scenarios          — list scenarios with filters
  GET /scenarios/random   — random scenario for practice
  GET /scenarios/categories — available categories
  GET /scenarios/{id}     — single scenario by ID
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.scenario_loader import (
    get_categories,
    get_random_scenario,
    get_scenario_by_id,
    get_scenarios,
)

router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])


class ScenarioResponse(BaseModel):
    """A single agentic interview scenario."""

    id: str
    track: str
    type: str
    role: str
    category: str
    difficulty: str
    question: str
    tags: list[str] = []
    ideal_answer_points: list[str] = []


class ScenarioListResponse(BaseModel):
    """List of scenarios with count."""

    items: list[ScenarioResponse]
    total: int


@router.get("", response_model=ScenarioListResponse)
async def list_scenarios(
    track: Optional[str] = None,
    role: Optional[str] = None,
    category: Optional[str] = None,
    interview_type: Optional[str] = None,
    difficulty: Optional[str] = None,
):
    """List agentic scenarios with optional filters.

    All filters are optional. Omitted filters match everything.
    """
    scenarios = get_scenarios(
        track=track,
        role=role,
        category=category,
        interview_type=interview_type,
        difficulty=difficulty,
    )
    return ScenarioListResponse(
        items=[ScenarioResponse(**s) for s in scenarios],
        total=len(scenarios),
    )


@router.get("/random", response_model=ScenarioResponse)
async def random_scenario(
    track: Optional[str] = "agentic",
    category: Optional[str] = None,
    interview_type: Optional[str] = None,
    difficulty: Optional[str] = None,
):
    """Get a random agentic scenario for practice."""
    scenario = get_random_scenario(
        track=track,
        category=category,
        interview_type=interview_type,
        difficulty=difficulty,
    )
    if not scenario:
        raise HTTPException(status_code=404, detail="No scenarios match the filters")
    return ScenarioResponse(**scenario)


@router.get("/categories", response_model=list[str])
async def list_categories(track: str = "agentic"):
    """Get available scenario categories for a track."""
    return get_categories(track=track)


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: str):
    """Get a specific scenario by ID."""
    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return ScenarioResponse(**scenario)
