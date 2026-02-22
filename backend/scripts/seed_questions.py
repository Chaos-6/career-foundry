"""
Seed the questions table with behavioral interview questions.

Questions are tagged by:
- role_tags: which roles this question is relevant for
- competency_tags: what behavioral competency it tests
- difficulty: standard, advanced, senior_plus
- level_band: entry, mid, senior, staff, manager (nullable for legacy questions)

Data sources:
- Original alpha code questions (normalized competency tags, no level_band)
- PDF question bank expansion (MLE, PM, TPM, EM) with level_band support

Run: python -m scripts.seed_questions (from backend/)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal, init_db
from app.models import Question

# ---------------------------------------------------------------------------
# Competency normalization map: old vocabulary → canonical vocabulary
# ---------------------------------------------------------------------------
COMPETENCY_MAP = {
    "feedback": "failure_resilience",
    "growth": "adaptability",
    "resilience": "failure_resilience",
    "debugging": "problem_solving",
    "trade_offs": "decision_making",
    "collaboration": "teamwork",
    "ambiguity": "adaptability",
    "stakeholder_management": "communication",
    "influence": "leadership",
    "prioritization": "decision_making",
    "scale": "technical_challenge",
    "data_driven": "decision_making",
    "customer_focus": "customer_obsession",
    "failure": "failure_resilience",
    "change_management": "adaptability",
    "conflict": "conflict_resolution",
}


def normalize_tags(tags: list[str]) -> list[str]:
    """Normalize competency tags and deduplicate."""
    normalized = []
    seen = set()
    for tag in tags:
        mapped = COMPETENCY_MAP.get(tag, tag)
        if mapped not in seen:
            normalized.append(mapped)
            seen.add(mapped)
    return normalized


# fmt: off

# ---------------------------------------------------------------------------
# Original questions from alpha code (now with level_band backfill)
# These are general questions with level_band assigned by difficulty heuristic:
#   standard → entry, advanced → mid, senior_plus → senior
#   Exception: EM-only questions → manager (matching PDF EM convention)
# Competency tags are written in the OLD vocabulary and normalized at insert.
# ---------------------------------------------------------------------------
LEGACY_QUESTIONS = [
    {"question_text": "Tell me about a time you had to work with someone whose working style was very different from yours.",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["collaboration", "conflict"], "difficulty": "standard", "level_band": "entry"},

    {"question_text": "Describe a time you led a team through a significant change or transformation.",
     "role_tags": ["EM", "PM"], "competency_tags": ["leadership", "change_management"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time you influenced a decision without having direct authority.",
     "role_tags": ["PM", "TPM", "MLE"], "competency_tags": ["influence", "leadership"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Give an example of when you mentored someone and saw them grow.",
     "role_tags": ["EM", "MLE"], "competency_tags": ["mentorship", "leadership"], "difficulty": "standard", "level_band": "entry"},

    {"question_text": "Tell me about a time you had to rally a demoralized team.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "resilience", "communication"], "difficulty": "advanced", "level_band": "manager"},

    {"question_text": "Tell me about the most technically challenging project you've worked on.",
     "role_tags": ["MLE", "TPM"], "competency_tags": ["technical_challenge", "problem_solving"], "difficulty": "standard", "level_band": "entry"},

    {"question_text": "Describe a time when you had to learn a new technology or domain quickly to solve a problem.",
     "role_tags": ["MLE", "TPM"], "competency_tags": ["growth", "technical_challenge", "ambiguity"], "difficulty": "standard", "level_band": "entry"},

    {"question_text": "Tell me about a time you identified a technical problem before it became a crisis.",
     "role_tags": ["MLE", "TPM", "EM"], "competency_tags": ["technical_challenge", "problem_solving"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe a time you had to optimize a system for performance at scale.",
     "role_tags": ["MLE", "TPM"], "competency_tags": ["scale", "technical_challenge"], "difficulty": "senior_plus", "level_band": "senior"},

    {"question_text": "Tell me about your biggest professional failure. What did you learn?",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["failure", "growth"], "difficulty": "standard", "level_band": "entry"},

    {"question_text": "Describe a project that failed. What would you do differently?",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["failure", "growth", "problem_solving"], "difficulty": "standard", "level_band": "entry"},

    {"question_text": "Tell me about a time your initial approach to a problem was wrong. How did you course correct?",
     "role_tags": ["MLE", "PM", "TPM"], "competency_tags": ["failure", "problem_solving", "growth"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time you had to manage competing stakeholder expectations.",
     "role_tags": ["PM", "TPM", "EM"], "competency_tags": ["stakeholder_management", "prioritization"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe a time when you had to deliver bad news to a stakeholder or customer.",
     "role_tags": ["PM", "EM"], "competency_tags": ["communication", "stakeholder_management"], "difficulty": "standard", "level_band": "entry"},

    {"question_text": "Tell me about a time you built consensus among stakeholders who initially disagreed.",
     "role_tags": ["PM", "TPM"], "competency_tags": ["stakeholder_management", "influence", "communication"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time when you had to make a decision with incomplete information.",
     "role_tags": ["PM", "MLE", "EM"], "competency_tags": ["decision_making", "ambiguity"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe how you've prioritized work when everything seemed equally urgent.",
     "role_tags": ["PM", "TPM", "EM"], "competency_tags": ["prioritization", "decision_making"], "difficulty": "standard", "level_band": "entry"},

    {"question_text": "Tell me about a time you had to cut scope to meet a deadline. How did you decide what to cut?",
     "role_tags": ["PM", "TPM", "EM"], "competency_tags": ["prioritization", "trade_offs"], "difficulty": "standard", "level_band": "entry"},

    {"question_text": "Tell me about a time you helped a struggling team member improve their performance.",
     "role_tags": ["EM"], "competency_tags": ["mentorship", "leadership", "feedback"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "Describe how you've built a high-performing team from scratch or significantly improved a team's performance.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "mentorship", "scale"], "difficulty": "senior_plus", "level_band": "manager"},

    {"question_text": "Tell me about a time you had to let someone go. How did you handle it?",
     "role_tags": ["EM"], "competency_tags": ["leadership", "conflict"], "difficulty": "senior_plus", "level_band": "manager"},

    {"question_text": "Tell me about a time you had to present a complex idea to senior leadership and gain their buy-in.",
     "role_tags": ["PM", "TPM", "EM"], "competency_tags": ["communication", "influence", "stakeholder_management"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe a situation where miscommunication led to a problem. How did you resolve it?",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["communication", "problem_solving"], "difficulty": "standard", "level_band": "entry"},

    {"question_text": "Tell me about a time you had to define a new process or system with no existing framework.",
     "role_tags": ["PM", "TPM", "EM"], "competency_tags": ["ambiguity", "leadership", "problem_solving"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe a time when requirements changed significantly mid-project. How did you adapt?",
     "role_tags": ["MLE", "PM", "TPM"], "competency_tags": ["ambiguity", "problem_solving", "resilience"], "difficulty": "standard", "level_band": "entry"},

    {"question_text": "Tell me about a time you started something completely new — no roadmap, no precedent.",
     "role_tags": ["MLE", "PM", "EM"], "competency_tags": ["ambiguity", "leadership", "ownership"], "difficulty": "senior_plus", "level_band": "senior"},

    {"question_text": "Tell me about a time you identified and drove a strategic initiative that changed how your organization operates.",
     "role_tags": ["PM", "EM"], "competency_tags": ["leadership", "scale", "influence"], "difficulty": "senior_plus", "level_band": "senior"},

    {"question_text": "Describe a time when you had to scale a team or process to handle rapid growth.",
     "role_tags": ["EM"], "competency_tags": ["scale", "leadership"], "difficulty": "senior_plus", "level_band": "manager"},

    {"question_text": "Tell me about a time you built something that served millions of users.",
     "role_tags": ["MLE", "PM"], "competency_tags": ["scale", "technical_challenge"], "difficulty": "senior_plus", "level_band": "senior"},

    {"question_text": "Tell me about a time you went above and beyond your role to solve a problem.",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["ownership", "problem_solving"], "difficulty": "standard", "level_band": "entry"},

    {"question_text": "Describe a time you identified an opportunity that nobody else saw and took action on it.",
     "role_tags": ["PM", "MLE"], "competency_tags": ["ownership", "leadership"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time you had to make a difficult ethical decision at work.",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["decision_making", "leadership"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time you deeply understood a customer's pain point and built a solution for it.",
     "role_tags": ["PM", "MLE"], "competency_tags": ["customer_focus", "problem_solving"], "difficulty": "standard", "level_band": "entry"},

    {"question_text": "Describe a time when user feedback caused you to significantly change your approach.",
     "role_tags": ["PM", "MLE"], "competency_tags": ["customer_focus", "growth"], "difficulty": "standard", "level_band": "entry"},

    {"question_text": "Tell me about a time you had to balance user needs against business constraints.",
     "role_tags": ["PM", "TPM"], "competency_tags": ["trade_offs", "customer_focus", "prioritization"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time you worked with a team from a completely different function to deliver a project.",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["collaboration", "communication"], "difficulty": "standard", "level_band": "entry"},

    {"question_text": "Describe a situation where you had to align multiple teams with different goals around a shared objective.",
     "role_tags": ["TPM", "PM", "EM"], "competency_tags": ["collaboration", "leadership", "influence"], "difficulty": "senior_plus", "level_band": "senior"},

    {"question_text": "Tell me about a time you designed and ran an experiment to validate a hypothesis.",
     "role_tags": ["MLE", "PM"], "competency_tags": ["data_driven", "problem_solving"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe a time when you had to make a decision without sufficient data. How did you proceed?",
     "role_tags": ["PM", "MLE", "EM"], "competency_tags": ["decision_making", "ambiguity"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time you introduced a new idea or approach that significantly improved a process or product.",
     "role_tags": ["MLE", "PM", "TPM"], "competency_tags": ["ownership", "problem_solving"], "difficulty": "standard", "level_band": "entry"},

    {"question_text": "Describe a time when you challenged the status quo and it led to a better outcome.",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["leadership", "ownership"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe a time you received pushback on a proposal. How did you handle it?",
     "role_tags": ["PM", "TPM", "MLE"], "competency_tags": ["conflict", "communication", "influence"], "difficulty": "standard", "level_band": "entry"},
]


# ---------------------------------------------------------------------------
# PDF Question Bank — Core Behavioral Questions
# These are shared across roles. Each row = unique (text, difficulty, level_band).
# Role tags are merged for identical text+difficulty+level_band.
# Competency tags are already in canonical vocabulary.
# ---------------------------------------------------------------------------
PDF_CORE_QUESTIONS = [
    # CORE-01: Harsh feedback
    {"question_text": "Tell me about a time when you received harsh feedback about your work. How did you respond and improve?",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["failure_resilience", "communication", "adaptability"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time when you received harsh feedback about your work. How did you respond and improve?",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["failure_resilience", "communication", "adaptability", "ownership"], "difficulty": "advanced", "level_band": "mid"},
    {"question_text": "Tell me about a time when you received harsh feedback about your work. How did you respond and improve?",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["leadership", "failure_resilience", "communication", "ownership"], "difficulty": "senior_plus", "level_band": "senior"},
    # EM variants (always Manager level_band)
    {"question_text": "Tell me about a time when you received harsh feedback about your work. How did you respond and improve?",
     "role_tags": ["EM"], "competency_tags": ["failure_resilience", "communication", "adaptability"], "difficulty": "standard", "level_band": "manager"},
    {"question_text": "Tell me about a time when you received harsh feedback about your work. How did you respond and improve?",
     "role_tags": ["EM"], "competency_tags": ["failure_resilience", "communication", "ownership"], "difficulty": "advanced", "level_band": "manager"},
    {"question_text": "Tell me about a time when you received harsh feedback about your work. How did you respond and improve?",
     "role_tags": ["EM"], "competency_tags": ["leadership", "failure_resilience", "communication", "ownership"], "difficulty": "senior_plus", "level_band": "manager"},

    # CORE-02: Ownership of failing project
    {"question_text": "Share a time when you took ownership of a failing project and delivered results.",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["ownership", "problem_solving", "failure_resilience"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Share a time when you took ownership of a failing project and delivered results.",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["ownership", "decision_making", "leadership", "adaptability"], "difficulty": "advanced", "level_band": "mid"},
    {"question_text": "Share a time when you took ownership of a failing project and delivered results.",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["leadership", "ownership", "decision_making", "failure_resilience"], "difficulty": "senior_plus", "level_band": "senior"},
    {"question_text": "Share a time when you took ownership of a failing project and delivered results.",
     "role_tags": ["EM"], "competency_tags": ["ownership", "problem_solving", "failure_resilience"], "difficulty": "standard", "level_band": "manager"},
    {"question_text": "Share a time when you took ownership of a failing project and delivered results.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "ownership", "decision_making", "adaptability"], "difficulty": "advanced", "level_band": "manager"},
    {"question_text": "Share a time when you took ownership of a failing project and delivered results.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "ownership", "decision_making", "technical_challenge"], "difficulty": "senior_plus", "level_band": "manager"},

    # CORE-03: Hiring a new team (PM, TPM, EM only)
    {"question_text": "Imagine that you are hiring a new team from scratch. Talk about your approach and factors you would consider.",
     "role_tags": ["PM", "TPM"], "competency_tags": ["leadership", "decision_making", "ownership", "teamwork"], "difficulty": "advanced", "level_band": "senior"},
    {"question_text": "Imagine that you are hiring a new team from scratch. Talk about your approach and factors you would consider.",
     "role_tags": ["PM", "TPM"], "competency_tags": ["leadership", "decision_making", "ownership", "adaptability"], "difficulty": "senior_plus", "level_band": "staff"},
    {"question_text": "Imagine that you are hiring a new team from scratch. Talk about your approach and factors you would consider.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "decision_making", "ownership", "teamwork"], "difficulty": "standard", "level_band": "manager"},
    {"question_text": "Imagine that you are hiring a new team from scratch. Talk about your approach and factors you would consider.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "decision_making", "ownership", "adaptability"], "difficulty": "advanced", "level_band": "manager"},

    # CORE-04 (MLE-03 / PM-04 / TPM-04): Unexpected roadblock
    {"question_text": "Tell me about a time when you encountered an unexpected, significant roadblock when working on a large initiative.",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["problem_solving", "adaptability", "technical_challenge"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time when you encountered an unexpected, significant roadblock when working on a large initiative.",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["decision_making", "problem_solving", "adaptability", "leadership"], "difficulty": "advanced", "level_band": "mid"},
    {"question_text": "Tell me about a time when you encountered an unexpected, significant roadblock when working on a large initiative.",
     "role_tags": ["MLE", "PM", "TPM"], "competency_tags": ["leadership", "decision_making", "problem_solving", "adaptability"], "difficulty": "senior_plus", "level_band": "senior"},
    {"question_text": "Tell me about a time when you encountered an unexpected, significant roadblock when working on a large initiative.",
     "role_tags": ["EM"], "competency_tags": ["problem_solving", "adaptability", "ownership"], "difficulty": "standard", "level_band": "manager"},
    {"question_text": "Tell me about a time when you encountered an unexpected, significant roadblock when working on a large initiative.",
     "role_tags": ["EM"], "competency_tags": ["decision_making", "leadership", "adaptability", "problem_solving"], "difficulty": "advanced", "level_band": "manager"},

    # CORE-05 (MLE-04 / PM-05 / TPM-05 / EM-05): Conflict between team members
    {"question_text": "Describe a situation where you had to resolve a conflict between two high-performing team members with opposing views on a technical direction.",
     "role_tags": ["MLE", "PM", "TPM"], "competency_tags": ["conflict_resolution", "teamwork", "communication", "technical_challenge"], "difficulty": "advanced", "level_band": "mid"},
    {"question_text": "Describe a situation where you had to resolve a conflict between two high-performing team members with opposing views on a technical direction.",
     "role_tags": ["MLE", "PM", "TPM"], "competency_tags": ["leadership", "conflict_resolution", "communication", "decision_making"], "difficulty": "senior_plus", "level_band": "senior"},
    {"question_text": "Describe a situation where you had to resolve a conflict between two high-performing team members with opposing views on a technical direction.",
     "role_tags": ["EM"], "competency_tags": ["conflict_resolution", "leadership", "communication", "teamwork"], "difficulty": "standard", "level_band": "manager"},
    {"question_text": "Describe a situation where you had to resolve a conflict between two high-performing team members with opposing views on a technical direction.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "conflict_resolution", "communication", "decision_making"], "difficulty": "advanced", "level_band": "manager"},

    # CORE-06 (MLE-05 / PM-06 / TPM-06 / EM-06): Scaling
    {"question_text": "Tell me about a time you successfully scaled a system, process, or product to meet significant growth or demand.",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["technical_challenge", "problem_solving", "innovation"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time you successfully scaled a system, process, or product to meet significant growth or demand.",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["technical_challenge", "innovation", "decision_making", "ownership"], "difficulty": "advanced", "level_band": "mid"},
    {"question_text": "Tell me about a time you successfully scaled a system, process, or product to meet significant growth or demand.",
     "role_tags": ["MLE", "PM", "TPM"], "competency_tags": ["leadership", "technical_challenge", "innovation", "ownership"], "difficulty": "senior_plus", "level_band": "senior"},
    {"question_text": "Tell me about a time you successfully scaled a system, process, or product to meet significant growth or demand.",
     "role_tags": ["EM"], "competency_tags": ["technical_challenge", "leadership", "problem_solving"], "difficulty": "standard", "level_band": "manager"},
    {"question_text": "Tell me about a time you successfully scaled a system, process, or product to meet significant growth or demand.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "technical_challenge", "decision_making", "ownership"], "difficulty": "advanced", "level_band": "manager"},

    # CORE-07 (MLE-06 / PM-07 / TPM-07 / EM-07): Unclear requirements
    {"question_text": "Describe a project where requirements were unclear or constantly changing - how did you move forward?",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["adaptability", "communication", "problem_solving"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Describe a project where requirements were unclear or constantly changing - how did you move forward?",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["adaptability", "ownership", "decision_making", "communication"], "difficulty": "advanced", "level_band": "mid"},
    {"question_text": "Describe a project where requirements were unclear or constantly changing - how did you move forward?",
     "role_tags": ["MLE", "PM", "TPM"], "competency_tags": ["leadership", "adaptability", "decision_making", "communication"], "difficulty": "senior_plus", "level_band": "senior"},
    {"question_text": "Describe a project where requirements were unclear or constantly changing - how did you move forward?",
     "role_tags": ["EM"], "competency_tags": ["adaptability", "leadership", "communication"], "difficulty": "standard", "level_band": "manager"},
    {"question_text": "Describe a project where requirements were unclear or constantly changing - how did you move forward?",
     "role_tags": ["EM"], "competency_tags": ["adaptability", "leadership", "decision_making", "communication"], "difficulty": "advanced", "level_band": "manager"},

    # CORE-08 (MLE-07 / PM-08 / TPM-08 / EM-08): New tool under constraints
    {"question_text": "Share an example of introducing a new tool, process, or feature under tight time or budget constraints.",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["innovation", "problem_solving", "adaptability"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Share an example of introducing a new tool, process, or feature under tight time or budget constraints.",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["innovation", "ownership", "decision_making", "adaptability"], "difficulty": "advanced", "level_band": "mid"},
    {"question_text": "Share an example of introducing a new tool, process, or feature under tight time or budget constraints.",
     "role_tags": ["MLE", "PM", "TPM"], "competency_tags": ["leadership", "innovation", "decision_making", "ownership"], "difficulty": "senior_plus", "level_band": "senior"},
    {"question_text": "Share an example of introducing a new tool, process, or feature under tight time or budget constraints.",
     "role_tags": ["EM"], "competency_tags": ["innovation", "leadership", "problem_solving"], "difficulty": "standard", "level_band": "manager"},
    {"question_text": "Share an example of introducing a new tool, process, or feature under tight time or budget constraints.",
     "role_tags": ["EM"], "competency_tags": ["innovation", "leadership", "decision_making", "ownership"], "difficulty": "advanced", "level_band": "manager"},

    # CORE-09 (MLE-08 / PM-09 / TPM-09 / EM-09): Bad news to leadership
    {"question_text": "Tell me about a time when you had to present bad news to senior leadership - how did you approach it?",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["communication", "failure_resilience", "adaptability"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time when you had to present bad news to senior leadership - how did you approach it?",
     "role_tags": ["MLE", "PM", "TPM", "EM"], "competency_tags": ["communication", "ownership", "decision_making", "failure_resilience"], "difficulty": "advanced", "level_band": "mid"},
    {"question_text": "Tell me about a time when you had to present bad news to senior leadership - how did you approach it?",
     "role_tags": ["MLE", "PM", "TPM"], "competency_tags": ["leadership", "communication", "ownership", "failure_resilience"], "difficulty": "senior_plus", "level_band": "senior"},
    {"question_text": "Tell me about a time when you had to present bad news to senior leadership - how did you approach it?",
     "role_tags": ["EM"], "competency_tags": ["communication", "leadership", "failure_resilience"], "difficulty": "standard", "level_band": "manager"},
    {"question_text": "Tell me about a time when you had to present bad news to senior leadership - how did you approach it?",
     "role_tags": ["EM"], "competency_tags": ["leadership", "communication", "ownership", "failure_resilience"], "difficulty": "advanced", "level_band": "manager"},

    # CORE-10 (MLE-09 / PM-10 / TPM-10 / EM-10): Developing junior member
    {"question_text": "Describe a situation where you developed a junior team member into a high-impact contributor.",
     "role_tags": ["MLE", "PM", "TPM"], "competency_tags": ["leadership", "mentorship", "teamwork", "communication"], "difficulty": "advanced", "level_band": "senior"},
    {"question_text": "Describe a situation where you developed a junior team member into a high-impact contributor.",
     "role_tags": ["MLE", "PM", "TPM"], "competency_tags": ["leadership", "mentorship", "ownership", "communication"], "difficulty": "senior_plus", "level_band": "staff"},
    {"question_text": "Describe a situation where you developed a junior team member into a high-impact contributor.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "mentorship", "communication", "teamwork"], "difficulty": "standard", "level_band": "manager"},
    {"question_text": "Describe a situation where you developed a junior team member into a high-impact contributor.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "mentorship", "ownership", "communication"], "difficulty": "advanced", "level_band": "manager"},
]


# ---------------------------------------------------------------------------
# PDF Question Bank — MLE-Specific Questions
# ---------------------------------------------------------------------------
PDF_MLE_QUESTIONS = [
    # MLE-SPEC-10: About yourself / ML experience
    {"question_text": "Tell me about yourself and your experience with machine learning.",
     "role_tags": ["MLE"], "competency_tags": ["communication", "technical_challenge"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about yourself and your experience with machine learning.",
     "role_tags": ["MLE"], "competency_tags": ["communication", "technical_challenge", "ownership"], "difficulty": "advanced", "level_band": "mid"},
    {"question_text": "Tell me about yourself and your experience with machine learning.",
     "role_tags": ["MLE"], "competency_tags": ["leadership", "communication", "ownership", "technical_challenge"], "difficulty": "senior_plus", "level_band": "senior"},

    # MLE-SPEC-11: Data and ML project
    {"question_text": "Give me an example of a project where you used data and machine learning.",
     "role_tags": ["MLE"], "competency_tags": ["technical_challenge", "problem_solving", "ownership"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Give me an example of a project where you used data and machine learning.",
     "role_tags": ["MLE"], "competency_tags": ["technical_challenge", "innovation", "ownership", "decision_making"], "difficulty": "advanced", "level_band": "mid"},

    # MLE-SPEC-12: Obstacle in ML project
    {"question_text": "Tell me about a time you faced an obstacle in an ML project and how you resolved it.",
     "role_tags": ["MLE"], "competency_tags": ["problem_solving", "technical_challenge", "failure_resilience"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time you faced an obstacle in an ML project and how you resolved it.",
     "role_tags": ["MLE"], "competency_tags": ["problem_solving", "technical_challenge", "adaptability", "ownership"], "difficulty": "advanced", "level_band": "mid"},

    # MLE-SPEC-13: Favorite ML project
    {"question_text": "Tell me about a recent or favorite ML project and some of the difficulties you had.",
     "role_tags": ["MLE"], "competency_tags": ["technical_challenge", "problem_solving", "adaptability"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a recent or favorite ML project and some of the difficulties you had.",
     "role_tags": ["MLE"], "competency_tags": ["technical_challenge", "innovation", "problem_solving", "ownership"], "difficulty": "advanced", "level_band": "mid"},

    # MLE-SPEC-14: Greatest accomplishment
    {"question_text": "Tell me about the greatest accomplishment of your career in AI or ML.",
     "role_tags": ["MLE"], "competency_tags": ["ownership", "technical_challenge", "communication"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about the greatest accomplishment of your career in AI or ML.",
     "role_tags": ["MLE"], "competency_tags": ["leadership", "ownership", "innovation", "technical_challenge"], "difficulty": "advanced", "level_band": "mid"},
    {"question_text": "Tell me about the greatest accomplishment of your career in AI or ML.",
     "role_tags": ["MLE"], "competency_tags": ["leadership", "ownership", "innovation", "decision_making"], "difficulty": "senior_plus", "level_band": "senior"},

    # MLE-SPEC-15: Struggled with colleague
    {"question_text": "Tell me about a time you struggled to work with one of your colleagues on a technical project.",
     "role_tags": ["MLE"], "competency_tags": ["teamwork", "conflict_resolution", "communication"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time you struggled to work with one of your colleagues on a technical project.",
     "role_tags": ["MLE"], "competency_tags": ["teamwork", "conflict_resolution", "communication", "adaptability"], "difficulty": "advanced", "level_band": "mid"},

    # MLE-SPEC-16: Resolve team conflict
    {"question_text": "Tell me about a time you had to resolve a conflict in a team.",
     "role_tags": ["MLE"], "competency_tags": ["conflict_resolution", "teamwork", "communication"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time you had to resolve a conflict in a team.",
     "role_tags": ["MLE"], "competency_tags": ["conflict_resolution", "teamwork", "leadership", "communication"], "difficulty": "advanced", "level_band": "mid"},

    # MLE-SPEC-17: Constructive feedback
    {"question_text": "Tell me about a time you were given feedback that was constructive.",
     "role_tags": ["MLE"], "competency_tags": ["failure_resilience", "adaptability", "communication"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time you were given feedback that was constructive.",
     "role_tags": ["MLE"], "competency_tags": ["failure_resilience", "adaptability", "ownership"], "difficulty": "advanced", "level_band": "mid"},

    # MLE-SPEC-18: Step up and take responsibility
    {"question_text": "Tell me about a time you had to step up and take responsibility for others.",
     "role_tags": ["MLE"], "competency_tags": ["leadership", "ownership", "teamwork"], "difficulty": "advanced", "level_band": "mid"},
    {"question_text": "Tell me about a time you had to step up and take responsibility for others.",
     "role_tags": ["MLE"], "competency_tags": ["leadership", "ownership", "decision_making"], "difficulty": "senior_plus", "level_band": "senior"},

    # MLE-SPEC-19: End-to-end ML pipeline
    {"question_text": "Tell me about a time you maintained an end-to-end ML pipeline in production. Describe your role and what you learned from it.",
     "role_tags": ["MLE"], "competency_tags": ["technical_challenge", "ownership", "problem_solving", "failure_resilience"], "difficulty": "advanced", "level_band": "mid"},
    {"question_text": "Tell me about a time you maintained an end-to-end ML pipeline in production. Describe your role and what you learned from it.",
     "role_tags": ["MLE"], "competency_tags": ["leadership", "technical_challenge", "ownership", "decision_making"], "difficulty": "senior_plus", "level_band": "senior"},

    # MLE-SPEC-20: Proudest project
    {"question_text": "What is your proudest project, and why?",
     "role_tags": ["MLE"], "competency_tags": ["ownership", "communication", "technical_challenge"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "What is your proudest project, and why?",
     "role_tags": ["MLE"], "competency_tags": ["ownership", "innovation", "communication", "technical_challenge"], "difficulty": "advanced", "level_band": "mid"},

    # MLE-SPEC-21: Complex findings to non-technical audience
    {"question_text": "Describe a time when you had to communicate complex technical findings to a non-technical audience. How did you ensure effective communication?",
     "role_tags": ["MLE"], "competency_tags": ["communication", "adaptability", "customer_obsession"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Describe a time when you had to communicate complex technical findings to a non-technical audience. How did you ensure effective communication?",
     "role_tags": ["MLE"], "competency_tags": ["communication", "leadership", "customer_obsession"], "difficulty": "advanced", "level_band": "mid"},

    # MLE-SPEC-22: Model not performing
    {"question_text": "Tell me about a time when your model did not perform as expected. How did you debug and improve it?",
     "role_tags": ["MLE"], "competency_tags": ["problem_solving", "failure_resilience", "technical_challenge"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time when your model did not perform as expected. How did you debug and improve it?",
     "role_tags": ["MLE"], "competency_tags": ["problem_solving", "technical_challenge", "innovation", "ownership"], "difficulty": "advanced", "level_band": "mid"},

    # MLE-SPEC-23: Prioritize multiple DS projects
    {"question_text": "Describe a situation where you had to prioritize multiple data science projects simultaneously. How did you manage your time and resources?",
     "role_tags": ["MLE"], "competency_tags": ["decision_making", "ownership", "adaptability", "problem_solving"], "difficulty": "advanced", "level_band": "mid"},
    {"question_text": "Describe a situation where you had to prioritize multiple data science projects simultaneously. How did you manage your time and resources?",
     "role_tags": ["MLE"], "competency_tags": ["leadership", "decision_making", "ownership", "adaptability"], "difficulty": "senior_plus", "level_band": "senior"},

    # MLE-SPEC-24: Statistical hypothesis testing
    {"question_text": "Give an example of a project where you applied statistical hypothesis testing to draw meaningful conclusions.",
     "role_tags": ["MLE"], "competency_tags": ["technical_challenge", "problem_solving", "decision_making"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Give an example of a project where you applied statistical hypothesis testing to draw meaningful conclusions.",
     "role_tags": ["MLE"], "competency_tags": ["technical_challenge", "problem_solving", "decision_making", "ownership"], "difficulty": "advanced", "level_band": "mid"},

    # MLE-SPEC-25: Missing or imbalanced data
    {"question_text": "Talk about a time when you had to deal with missing or imbalanced data in your analysis. How did you handle it?",
     "role_tags": ["MLE"], "competency_tags": ["technical_challenge", "problem_solving", "adaptability"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Talk about a time when you had to deal with missing or imbalanced data in your analysis. How did you handle it?",
     "role_tags": ["MLE"], "competency_tags": ["technical_challenge", "innovation", "problem_solving"], "difficulty": "advanced", "level_band": "mid"},

    # MLE-SPEC-26: Limitations of ML model to stakeholders
    {"question_text": "Describe a challenging situation where you had to explain the limitations of a machine learning model to stakeholders.",
     "role_tags": ["MLE"], "competency_tags": ["communication", "customer_obsession", "technical_challenge", "adaptability"], "difficulty": "advanced", "level_band": "mid"},

    # MLE-SPEC-27: Staying current with ML/AI
    {"question_text": "Tell me about a project where you had to stay up to date with the latest developments in ML or AI. How did you keep your skills current?",
     "role_tags": ["MLE"], "competency_tags": ["adaptability", "innovation", "ownership"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a project where you had to stay up to date with the latest developments in ML or AI. How did you keep your skills current?",
     "role_tags": ["MLE"], "competency_tags": ["innovation", "ownership", "adaptability", "technical_challenge"], "difficulty": "advanced", "level_band": "mid"},

    # MLE-SPEC-28: Accuracy vs inference time trade-off
    {"question_text": "Describe a time when you had to make a trade-off between model accuracy and inference time or computational cost.",
     "role_tags": ["MLE"], "competency_tags": ["decision_making", "technical_challenge", "problem_solving"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Describe a time when you had to make a trade-off between model accuracy and inference time or computational cost.",
     "role_tags": ["MLE"], "competency_tags": ["decision_making", "technical_challenge", "ownership", "adaptability"], "difficulty": "advanced", "level_band": "mid"},

    # MLE-SPEC-29: Deploy model with engineers
    {"question_text": "Tell me about a time when you had to work with engineers to deploy a model into production. What challenges did you face?",
     "role_tags": ["MLE"], "competency_tags": ["teamwork", "technical_challenge", "communication", "problem_solving"], "difficulty": "advanced", "level_band": "mid"},
    {"question_text": "Tell me about a time when you had to work with engineers to deploy a model into production. What challenges did you face?",
     "role_tags": ["MLE"], "competency_tags": ["leadership", "teamwork", "technical_challenge", "ownership"], "difficulty": "senior_plus", "level_band": "senior"},

    # MLE-SPEC-30: Ambiguous requirements in AI/ML
    {"question_text": "Give an example of how you have handled ambiguous requirements in an AI or ML project.",
     "role_tags": ["MLE"], "competency_tags": ["adaptability", "problem_solving", "communication"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Give an example of how you have handled ambiguous requirements in an AI or ML project.",
     "role_tags": ["MLE"], "competency_tags": ["adaptability", "ownership", "decision_making", "communication"], "difficulty": "advanced", "level_band": "mid"},

    # --- Staff-level MLE questions ---
    # MLE-STAFF-01: ML system architecture at org level
    {"question_text": "Tell me about a time you defined the ML platform or infrastructure strategy for your organization. How did you evaluate build vs. buy and drive adoption?",
     "role_tags": ["MLE"], "competency_tags": ["leadership", "technical_challenge", "decision_making", "ownership"], "difficulty": "senior_plus", "level_band": "staff"},
    # MLE-STAFF-02: Cross-org technical influence
    {"question_text": "Describe a situation where you drove a technical standard or best practice across multiple teams or orgs. How did you get buy-in and measure impact?",
     "role_tags": ["MLE"], "competency_tags": ["leadership", "communication", "innovation", "ownership"], "difficulty": "senior_plus", "level_band": "staff"},
    # MLE-STAFF-03: Mentoring senior engineers
    {"question_text": "Tell me about a time you mentored a senior engineer through a career-defining technical challenge. What was your approach and what did they achieve?",
     "role_tags": ["MLE"], "competency_tags": ["mentorship", "leadership", "communication", "ownership"], "difficulty": "senior_plus", "level_band": "staff"},
    # MLE-STAFF-04: Production ML at scale
    {"question_text": "Tell me about a time you designed an ML system that needed to serve predictions at massive scale with strict latency requirements. What trade-offs did you make?",
     "role_tags": ["MLE"], "competency_tags": ["technical_challenge", "decision_making", "innovation", "ownership"], "difficulty": "senior_plus", "level_band": "staff"},
    # MLE-STAFF-05: Research to production
    {"question_text": "Describe a time you bridged the gap between ML research and production engineering. How did you translate cutting-edge research into a reliable, maintainable system?",
     "role_tags": ["MLE"], "competency_tags": ["technical_challenge", "innovation", "leadership", "adaptability"], "difficulty": "senior_plus", "level_band": "staff"},
    # MLE-STAFF-06: Technical vision and roadmap
    {"question_text": "Tell me about a time you set the technical vision and multi-year roadmap for an ML team or platform. How did you align stakeholders and adapt the plan over time?",
     "role_tags": ["MLE"], "competency_tags": ["leadership", "decision_making", "communication", "ownership"], "difficulty": "senior_plus", "level_band": "staff"},

    # --- Manager-level MLE questions ---
    # MLE-MGR-01: Building an ML team
    {"question_text": "Tell me about a time you built an ML team from scratch or significantly grew one. How did you define roles, hire, and set the team up for success?",
     "role_tags": ["MLE"], "competency_tags": ["leadership", "decision_making", "ownership", "teamwork"], "difficulty": "advanced", "level_band": "manager"},
    # MLE-MGR-02: Balancing research and delivery
    {"question_text": "Describe how you balanced research exploration with delivery commitments on your ML team. How did you manage stakeholder expectations?",
     "role_tags": ["MLE"], "competency_tags": ["decision_making", "leadership", "communication", "adaptability"], "difficulty": "advanced", "level_band": "manager"},
    # MLE-MGR-03: Managing ML technical debt
    {"question_text": "Tell me about a time you had to make a strategic decision about ML technical debt — when to pay it down vs. push forward with new features.",
     "role_tags": ["MLE"], "competency_tags": ["decision_making", "technical_challenge", "leadership", "ownership"], "difficulty": "advanced", "level_band": "manager"},
    # MLE-MGR-04: Cross-functional ML alignment
    {"question_text": "Describe a time you aligned your ML team's priorities with product, engineering, and business stakeholders who had competing needs.",
     "role_tags": ["MLE"], "competency_tags": ["leadership", "communication", "conflict_resolution", "decision_making"], "difficulty": "advanced", "level_band": "manager"},
    # MLE-MGR-05: Performance management for ML engineers
    {"question_text": "Tell me about a time you had to address performance issues on your ML team. How did you balance technical mentoring with management accountability?",
     "role_tags": ["MLE"], "competency_tags": ["leadership", "mentorship", "conflict_resolution", "communication"], "difficulty": "standard", "level_band": "manager"},
    # MLE-MGR-06: ML incident management
    {"question_text": "Tell me about a production ML failure or model degradation incident you managed. How did you handle the crisis and what processes did you put in place afterward?",
     "role_tags": ["MLE"], "competency_tags": ["failure_resilience", "leadership", "decision_making", "technical_challenge"], "difficulty": "advanced", "level_band": "manager"},
]


# ---------------------------------------------------------------------------
# PDF Question Bank — PM-Specific Questions
# ---------------------------------------------------------------------------
PDF_PM_QUESTIONS = [
    {"question_text": "Tell me about yourself and why you want to be a Product Manager.",
     "role_tags": ["PM"], "competency_tags": ["communication", "ownership", "customer_obsession"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about yourself and why you want to be a Product Manager.",
     "role_tags": ["PM"], "competency_tags": ["communication", "decision_making", "ownership"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time when you made an unpopular decision.",
     "role_tags": ["PM"], "competency_tags": ["decision_making", "ownership", "communication"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time when you made an unpopular decision.",
     "role_tags": ["PM"], "competency_tags": ["leadership", "decision_making", "communication", "conflict_resolution"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time when you had to motivate a team.",
     "role_tags": ["PM"], "competency_tags": ["leadership", "teamwork", "communication"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time when you had to motivate a team.",
     "role_tags": ["PM"], "competency_tags": ["leadership", "communication", "adaptability"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time when you received negative user feedback on a product you worked on.",
     "role_tags": ["PM"], "competency_tags": ["customer_obsession", "failure_resilience", "communication"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time when you received negative user feedback on a product you worked on.",
     "role_tags": ["PM"], "competency_tags": ["customer_obsession", "ownership", "failure_resilience", "adaptability"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time when you disagreed with an important stakeholder.",
     "role_tags": ["PM"], "competency_tags": ["conflict_resolution", "communication", "teamwork"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time when you disagreed with an important stakeholder.",
     "role_tags": ["PM"], "competency_tags": ["leadership", "conflict_resolution", "communication", "decision_making"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time when you had to handle conflicting priorities.",
     "role_tags": ["PM"], "competency_tags": ["decision_making", "adaptability", "problem_solving"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time when you had to handle conflicting priorities.",
     "role_tags": ["PM"], "competency_tags": ["decision_making", "ownership", "adaptability", "leadership"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time when you failed, or one of your products failed.",
     "role_tags": ["PM"], "competency_tags": ["failure_resilience", "problem_solving", "ownership"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time when you failed, or one of your products failed.",
     "role_tags": ["PM"], "competency_tags": ["failure_resilience", "ownership", "decision_making", "adaptability"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Why do you want to work for this company?",
     "role_tags": ["PM"], "competency_tags": ["communication", "customer_obsession", "ownership"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Why do you want to work for this company?",
     "role_tags": ["PM"], "competency_tags": ["communication", "decision_making", "customer_obsession"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a challenging issue or challenge you took on.",
     "role_tags": ["PM"], "competency_tags": ["problem_solving", "ownership", "technical_challenge"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a challenging issue or challenge you took on.",
     "role_tags": ["PM"], "competency_tags": ["leadership", "problem_solving", "ownership", "adaptability"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "How do you interact with customers or users?",
     "role_tags": ["PM"], "competency_tags": ["customer_obsession", "communication", "adaptability"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "How do you interact with customers or users?",
     "role_tags": ["PM"], "competency_tags": ["customer_obsession", "communication", "leadership"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about how you have overcome product failures or challenges or poor feedback.",
     "role_tags": ["PM"], "competency_tags": ["failure_resilience", "problem_solving", "customer_obsession"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about how you have overcome product failures or challenges or poor feedback.",
     "role_tags": ["PM"], "competency_tags": ["failure_resilience", "ownership", "decision_making", "customer_obsession"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time you had to influence someone.",
     "role_tags": ["PM"], "competency_tags": ["communication", "leadership", "teamwork"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time you had to influence someone.",
     "role_tags": ["PM"], "competency_tags": ["leadership", "communication", "decision_making"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a mistake you made and how you handled it.",
     "role_tags": ["PM"], "competency_tags": ["failure_resilience", "ownership", "communication"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a mistake you made and how you handled it.",
     "role_tags": ["PM"], "competency_tags": ["failure_resilience", "ownership", "adaptability", "decision_making"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "One executive says that Feature A is more important, and another executive says Feature B is more important. How do you choose which one to implement?",
     "role_tags": ["PM"], "competency_tags": ["decision_making", "communication", "conflict_resolution"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "One executive says that Feature A is more important, and another executive says Feature B is more important. How do you choose which one to implement?",
     "role_tags": ["PM"], "competency_tags": ["leadership", "decision_making", "customer_obsession", "communication"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time you used data to make a decision.",
     "role_tags": ["PM"], "competency_tags": ["decision_making", "problem_solving", "communication"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time you used data to make a decision.",
     "role_tags": ["PM"], "competency_tags": ["decision_making", "ownership", "technical_challenge"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe a time you had to persuade a team to follow your direction.",
     "role_tags": ["PM"], "competency_tags": ["leadership", "communication", "teamwork"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Describe a time you had to persuade a team to follow your direction.",
     "role_tags": ["PM"], "competency_tags": ["leadership", "communication", "decision_making"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time when you had to balance engineering limitations with customer requirements.",
     "role_tags": ["PM"], "competency_tags": ["technical_challenge", "customer_obsession", "communication"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time when you had to balance engineering limitations with customer requirements.",
     "role_tags": ["PM"], "competency_tags": ["decision_making", "technical_challenge", "customer_obsession", "ownership"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe a situation where you had to make a difficult decision that affected a product's roadmap. What was the outcome?",
     "role_tags": ["PM"], "competency_tags": ["decision_making", "leadership", "ownership", "communication"], "difficulty": "advanced", "level_band": "mid"},
    {"question_text": "Describe a situation where you had to make a difficult decision that affected a product's roadmap. What was the outcome?",
     "role_tags": ["PM"], "competency_tags": ["leadership", "decision_making", "ownership", "customer_obsession"], "difficulty": "senior_plus", "level_band": "senior"},

    {"question_text": "Tell me about an instance where you implemented user feedback into a product. What was the impact?",
     "role_tags": ["PM"], "competency_tags": ["customer_obsession", "innovation", "communication"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about an instance where you implemented user feedback into a product. What was the impact?",
     "role_tags": ["PM"], "competency_tags": ["customer_obsession", "innovation", "ownership", "decision_making"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe a time when you had to prioritize features with limited resources.",
     "role_tags": ["PM"], "competency_tags": ["decision_making", "adaptability", "customer_obsession"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Describe a time when you had to prioritize features with limited resources.",
     "role_tags": ["PM"], "competency_tags": ["decision_making", "ownership", "customer_obsession", "leadership"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a product launch that did not go as planned. How did you handle it?",
     "role_tags": ["PM"], "competency_tags": ["failure_resilience", "problem_solving", "adaptability"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a product launch that did not go as planned. How did you handle it?",
     "role_tags": ["PM"], "competency_tags": ["failure_resilience", "ownership", "decision_making", "leadership"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Give an example of a time when you had to say no to a stakeholder request.",
     "role_tags": ["PM"], "competency_tags": ["decision_making", "communication", "conflict_resolution"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Give an example of a time when you had to say no to a stakeholder request.",
     "role_tags": ["PM"], "competency_tags": ["leadership", "decision_making", "communication", "customer_obsession"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe a situation where you had to work with cross-functional teams under tight deadlines.",
     "role_tags": ["PM"], "competency_tags": ["teamwork", "adaptability", "communication"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Describe a situation where you had to work with cross-functional teams under tight deadlines.",
     "role_tags": ["PM"], "competency_tags": ["leadership", "teamwork", "adaptability", "ownership"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time when data contradicted your intuition. What did you do?",
     "role_tags": ["PM"], "competency_tags": ["decision_making", "problem_solving", "communication"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time when data contradicted your intuition. What did you do?",
     "role_tags": ["PM"], "competency_tags": ["decision_making", "ownership", "adaptability", "customer_obsession"], "difficulty": "advanced", "level_band": "mid"},

    # --- Staff-level PM questions ---
    # PM-STAFF-01: Product vision and multi-year strategy
    {"question_text": "Tell me about a time you defined or redefined the product vision for a major product area. How did you align the organization and measure progress toward that vision?",
     "role_tags": ["PM"], "competency_tags": ["leadership", "decision_making", "customer_obsession", "ownership"], "difficulty": "senior_plus", "level_band": "staff"},
    # PM-STAFF-02: Influencing company-wide strategy
    {"question_text": "Describe a time when you influenced company-wide product strategy from a non-executive position. How did you build the case and get leadership buy-in?",
     "role_tags": ["PM"], "competency_tags": ["leadership", "communication", "decision_making", "ownership"], "difficulty": "senior_plus", "level_band": "staff"},
    # PM-STAFF-03: Platform or ecosystem thinking
    {"question_text": "Tell me about a product decision you made that created a platform or ecosystem effect — where the value compounded across multiple teams or products.",
     "role_tags": ["PM"], "competency_tags": ["innovation", "leadership", "decision_making", "technical_challenge"], "difficulty": "senior_plus", "level_band": "staff"},
    # PM-STAFF-04: Killing a product or feature
    {"question_text": "Tell me about a time you decided to sunset or kill a product, feature, or initiative that others were invested in. How did you navigate the organizational impact?",
     "role_tags": ["PM"], "competency_tags": ["decision_making", "leadership", "communication", "conflict_resolution"], "difficulty": "senior_plus", "level_band": "staff"},
    # PM-STAFF-05: Mentoring PMs
    {"question_text": "Describe how you've mentored other product managers and elevated the craft of product management in your organization.",
     "role_tags": ["PM"], "competency_tags": ["mentorship", "leadership", "communication", "ownership"], "difficulty": "senior_plus", "level_band": "staff"},
    # PM-STAFF-06: Zero-to-one product
    {"question_text": "Tell me about a zero-to-one product you conceived and shipped. How did you validate the opportunity, navigate uncertainty, and drive it from idea to launched product?",
     "role_tags": ["PM"], "competency_tags": ["ownership", "innovation", "decision_making", "customer_obsession"], "difficulty": "senior_plus", "level_band": "staff"},

    # --- Manager-level PM questions ---
    # PM-MGR-01: Building a PM team
    {"question_text": "Tell me about a time you built or restructured a product management team. How did you define roles, hire, and set the culture?",
     "role_tags": ["PM"], "competency_tags": ["leadership", "decision_making", "ownership", "teamwork"], "difficulty": "advanced", "level_band": "manager"},
    # PM-MGR-02: Coaching PMs through ambiguity
    {"question_text": "Describe a time you coached a PM through a highly ambiguous product problem. How did you guide without dictating?",
     "role_tags": ["PM"], "competency_tags": ["mentorship", "leadership", "communication", "adaptability"], "difficulty": "advanced", "level_band": "manager"},
    # PM-MGR-03: Portfolio prioritization
    {"question_text": "Tell me about a time you had to prioritize across multiple product areas or teams competing for the same resources. How did you make the call?",
     "role_tags": ["PM"], "competency_tags": ["decision_making", "leadership", "communication", "ownership"], "difficulty": "advanced", "level_band": "manager"},
    # PM-MGR-04: PM performance and growth
    {"question_text": "Describe how you evaluate and develop the performance of product managers on your team. How do you handle underperformance?",
     "role_tags": ["PM"], "competency_tags": ["leadership", "mentorship", "conflict_resolution", "communication"], "difficulty": "standard", "level_band": "manager"},
    # PM-MGR-05: Aligning product and engineering leadership
    {"question_text": "Tell me about a time you had to align product and engineering leadership on a contentious technical or product decision.",
     "role_tags": ["PM"], "competency_tags": ["leadership", "communication", "conflict_resolution", "decision_making"], "difficulty": "advanced", "level_band": "manager"},
    # PM-MGR-06: Product org strategy
    {"question_text": "Tell me about how you've set the strategic direction for a product organization. How did you translate business goals into a product roadmap?",
     "role_tags": ["PM"], "competency_tags": ["leadership", "decision_making", "ownership", "customer_obsession"], "difficulty": "advanced", "level_band": "manager"},
]


# ---------------------------------------------------------------------------
# PDF Question Bank — TPM-Specific Questions
# ---------------------------------------------------------------------------
PDF_TPM_QUESTIONS = [
    {"question_text": "Tell me about yourself and your technical background.",
     "role_tags": ["TPM"], "competency_tags": ["communication", "technical_challenge", "ownership"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about yourself and your technical background.",
     "role_tags": ["TPM"], "competency_tags": ["communication", "technical_challenge", "leadership"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe a time when you had to bridge the gap between technical and non-technical stakeholders.",
     "role_tags": ["TPM"], "competency_tags": ["communication", "teamwork", "adaptability"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Describe a time when you had to bridge the gap between technical and non-technical stakeholders.",
     "role_tags": ["TPM"], "competency_tags": ["leadership", "communication", "customer_obsession", "adaptability"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time when you had to make a technical trade-off decision. How did you evaluate the options?",
     "role_tags": ["TPM"], "competency_tags": ["decision_making", "technical_challenge", "problem_solving"], "difficulty": "advanced", "level_band": "mid"},
    {"question_text": "Tell me about a time when you had to make a technical trade-off decision. How did you evaluate the options?",
     "role_tags": ["TPM"], "competency_tags": ["leadership", "decision_making", "technical_challenge", "ownership"], "difficulty": "senior_plus", "level_band": "senior"},

    {"question_text": "Give an example of when you had to explain complex technical concepts to business stakeholders.",
     "role_tags": ["TPM"], "competency_tags": ["communication", "technical_challenge", "adaptability"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Give an example of when you had to explain complex technical concepts to business stakeholders.",
     "role_tags": ["TPM"], "competency_tags": ["communication", "customer_obsession", "leadership"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe a situation where you had to push back on engineering estimates or timelines.",
     "role_tags": ["TPM"], "competency_tags": ["conflict_resolution", "communication", "decision_making", "ownership"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time when you had to work with engineers to define technical requirements.",
     "role_tags": ["TPM"], "competency_tags": ["teamwork", "communication", "technical_challenge"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a time when you had to work with engineers to define technical requirements.",
     "role_tags": ["TPM"], "competency_tags": ["leadership", "teamwork", "technical_challenge", "ownership"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Share an experience where you had to balance technical debt with feature development.",
     "role_tags": ["TPM"], "competency_tags": ["decision_making", "technical_challenge", "ownership", "adaptability"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe a time when you had to evaluate different technical architectures or approaches.",
     "role_tags": ["TPM"], "competency_tags": ["technical_challenge", "decision_making", "problem_solving"], "difficulty": "advanced", "level_band": "mid"},
    {"question_text": "Describe a time when you had to evaluate different technical architectures or approaches.",
     "role_tags": ["TPM"], "competency_tags": ["leadership", "decision_making", "technical_challenge", "ownership"], "difficulty": "senior_plus", "level_band": "senior"},

    {"question_text": "Tell me about a technical project that failed. What did you learn?",
     "role_tags": ["TPM"], "competency_tags": ["failure_resilience", "problem_solving", "technical_challenge"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Tell me about a technical project that failed. What did you learn?",
     "role_tags": ["TPM"], "competency_tags": ["failure_resilience", "ownership", "decision_making", "technical_challenge"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Give an example of how you have worked with API design or system architecture decisions.",
     "role_tags": ["TPM"], "competency_tags": ["technical_challenge", "decision_making", "ownership"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe a situation where you had to navigate technical constraints while meeting business objectives.",
     "role_tags": ["TPM"], "competency_tags": ["decision_making", "technical_challenge", "customer_obsession"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time when you disagreed with an engineering decision. How did you handle it?",
     "role_tags": ["TPM"], "competency_tags": ["conflict_resolution", "communication", "leadership", "decision_making"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Share an example of when you had to learn a new technology quickly to support your product.",
     "role_tags": ["TPM"], "competency_tags": ["adaptability", "technical_challenge", "ownership"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Share an example of when you had to learn a new technology quickly to support your product.",
     "role_tags": ["TPM"], "competency_tags": ["adaptability", "innovation", "technical_challenge"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe how you have collaborated with engineering teams on technical roadmap planning.",
     "role_tags": ["TPM"], "competency_tags": ["leadership", "teamwork", "decision_making", "communication"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Tell me about a time when you had to prioritize technical features versus user-facing features.",
     "role_tags": ["TPM"], "competency_tags": ["decision_making", "customer_obsession", "technical_challenge"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Give an example of when you had to communicate technical limitations to customers or sales teams.",
     "role_tags": ["TPM"], "competency_tags": ["communication", "customer_obsession", "adaptability"], "difficulty": "standard", "level_band": "entry"},
    {"question_text": "Give an example of when you had to communicate technical limitations to customers or sales teams.",
     "role_tags": ["TPM"], "competency_tags": ["communication", "customer_obsession", "leadership"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe a situation where you led a technical integration or migration project.",
     "role_tags": ["TPM"], "competency_tags": ["leadership", "technical_challenge", "ownership", "problem_solving"], "difficulty": "advanced", "level_band": "senior"},
    {"question_text": "Describe a situation where you led a technical integration or migration project.",
     "role_tags": ["TPM"], "competency_tags": ["leadership", "decision_making", "ownership", "technical_challenge"], "difficulty": "senior_plus", "level_band": "staff"},

    {"question_text": "Tell me about a time when you had to make security or performance trade-offs in your product.",
     "role_tags": ["TPM"], "competency_tags": ["decision_making", "technical_challenge", "problem_solving"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Share an experience where you worked on developer tools, APIs, or platform products.",
     "role_tags": ["TPM"], "competency_tags": ["technical_challenge", "innovation", "customer_obsession"], "difficulty": "advanced", "level_band": "mid"},

    {"question_text": "Describe how you have handled technical incidents or outages affecting your product.",
     "role_tags": ["TPM"], "competency_tags": ["failure_resilience", "decision_making", "technical_challenge", "communication"], "difficulty": "advanced", "level_band": "mid"},

    # --- Staff-level TPM questions ---
    # TPM-STAFF-01: Technical strategy across programs
    {"question_text": "Tell me about a time you defined the technical strategy for a program spanning multiple teams and systems. How did you drive alignment and manage dependencies?",
     "role_tags": ["TPM"], "competency_tags": ["leadership", "technical_challenge", "decision_making", "ownership"], "difficulty": "senior_plus", "level_band": "staff"},
    # TPM-STAFF-02: Org-wide process improvement
    {"question_text": "Describe a time you identified and drove a process improvement that changed how your engineering organization ships software. What resistance did you face?",
     "role_tags": ["TPM"], "competency_tags": ["leadership", "innovation", "communication", "ownership"], "difficulty": "senior_plus", "level_band": "staff"},
    # TPM-STAFF-03: Architecture influence without authority
    {"question_text": "Tell me about a time you influenced a major architectural decision across teams you didn't manage. How did you build credibility and drive consensus?",
     "role_tags": ["TPM"], "competency_tags": ["leadership", "communication", "technical_challenge", "conflict_resolution"], "difficulty": "senior_plus", "level_band": "staff"},
    # TPM-STAFF-04: Large-scale migration or platform shift
    {"question_text": "Describe a large-scale platform migration or infrastructure overhaul you led. How did you plan for risk, handle rollbacks, and coordinate across the organization?",
     "role_tags": ["TPM"], "competency_tags": ["technical_challenge", "leadership", "decision_making", "problem_solving"], "difficulty": "senior_plus", "level_band": "staff"},
    # TPM-STAFF-05: Mentoring TPMs
    {"question_text": "Tell me about how you've mentored other TPMs or technical leaders. How did you help them develop their technical depth and stakeholder management skills?",
     "role_tags": ["TPM"], "competency_tags": ["mentorship", "leadership", "communication", "ownership"], "difficulty": "senior_plus", "level_band": "staff"},
    # TPM-STAFF-06: Technical due diligence
    {"question_text": "Tell me about a time you conducted technical due diligence for a major product, partnership, or acquisition decision. How did you assess technical risk?",
     "role_tags": ["TPM"], "competency_tags": ["technical_challenge", "decision_making", "ownership", "communication"], "difficulty": "senior_plus", "level_band": "staff"},

    # --- Manager-level TPM questions ---
    # TPM-MGR-01: Building a TPM team
    {"question_text": "Tell me about a time you built or grew a TPM function within an organization. How did you define the role's value and hire the right people?",
     "role_tags": ["TPM"], "competency_tags": ["leadership", "decision_making", "ownership", "teamwork"], "difficulty": "advanced", "level_band": "manager"},
    # TPM-MGR-02: Program portfolio management
    {"question_text": "Describe how you prioritize and allocate TPM resources across a portfolio of programs. How do you decide where to invest TPM time?",
     "role_tags": ["TPM"], "competency_tags": ["decision_making", "leadership", "ownership", "adaptability"], "difficulty": "advanced", "level_band": "manager"},
    # TPM-MGR-03: Developing TPMs
    {"question_text": "Tell me about a time you helped a TPM grow from good to great. What skills did you focus on and how did you coach them?",
     "role_tags": ["TPM"], "competency_tags": ["mentorship", "leadership", "communication", "ownership"], "difficulty": "standard", "level_band": "manager"},
    # TPM-MGR-04: Engineering partnership
    {"question_text": "Describe how you've built strong partnerships between TPM and engineering leadership. How do you ensure TPMs are seen as strategic partners, not just project trackers?",
     "role_tags": ["TPM"], "competency_tags": ["leadership", "communication", "teamwork", "ownership"], "difficulty": "advanced", "level_band": "manager"},
    # TPM-MGR-05: Crisis management as a leader
    {"question_text": "Tell me about a major program crisis you managed as a TPM leader. How did you coordinate the response and what systemic changes did you drive afterward?",
     "role_tags": ["TPM"], "competency_tags": ["failure_resilience", "leadership", "decision_making", "communication"], "difficulty": "advanced", "level_band": "manager"},
    # TPM-MGR-06: Cross-org technical governance
    {"question_text": "Describe a time you established or improved technical governance processes across multiple engineering teams. How did you balance oversight with engineering autonomy?",
     "role_tags": ["TPM"], "competency_tags": ["leadership", "decision_making", "communication", "technical_challenge"], "difficulty": "advanced", "level_band": "manager"},
]


# ---------------------------------------------------------------------------
# PDF Question Bank — EM-Specific Questions (People Management)
# All EM questions use level_band="manager"
# ---------------------------------------------------------------------------
PDF_EM_PEOPLE_QUESTIONS = [
    {"question_text": "Tell me about yourself and your management philosophy.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "communication", "ownership"], "difficulty": "standard", "level_band": "manager"},
    {"question_text": "Tell me about yourself and your management philosophy.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "communication", "decision_making"], "difficulty": "advanced", "level_band": "manager"},

    {"question_text": "Why do you want to be an engineering manager?",
     "role_tags": ["EM"], "competency_tags": ["leadership", "communication", "ownership"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "How do you manage team performance?",
     "role_tags": ["EM"], "competency_tags": ["leadership", "decision_making", "ownership"], "difficulty": "standard", "level_band": "manager"},
    {"question_text": "How do you manage team performance?",
     "role_tags": ["EM"], "competency_tags": ["leadership", "decision_making", "adaptability", "communication"], "difficulty": "advanced", "level_band": "manager"},

    {"question_text": "Tell me about a time you made a mistake as a manager.",
     "role_tags": ["EM"], "competency_tags": ["failure_resilience", "ownership", "communication"], "difficulty": "standard", "level_band": "manager"},
    {"question_text": "Tell me about a time you made a mistake as a manager.",
     "role_tags": ["EM"], "competency_tags": ["failure_resilience", "ownership", "adaptability", "leadership"], "difficulty": "advanced", "level_band": "manager"},

    {"question_text": "How do you deal with low performers?",
     "role_tags": ["EM"], "competency_tags": ["leadership", "conflict_resolution", "communication", "decision_making"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "How do you handle conflicts in your team?",
     "role_tags": ["EM"], "competency_tags": ["conflict_resolution", "leadership", "communication", "teamwork"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "How do you deal with high performers and keep them engaged?",
     "role_tags": ["EM"], "competency_tags": ["leadership", "communication", "adaptability"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "Tell me about a time you developed and retained team members.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "mentorship", "communication", "ownership"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "How do you manage your team's career growth?",
     "role_tags": ["EM"], "competency_tags": ["leadership", "mentorship", "decision_making", "ownership"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "How would you grow a team by 10x?",
     "role_tags": ["EM"], "competency_tags": ["leadership", "decision_making", "ownership", "adaptability"], "difficulty": "advanced", "level_band": "manager"},

    {"question_text": "Tell me about a difficult employee situation that you handled well or not so well.",
     "role_tags": ["EM"], "competency_tags": ["conflict_resolution", "leadership", "communication", "failure_resilience"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "What would you do with someone that had stayed at the same level for too long?",
     "role_tags": ["EM"], "competency_tags": ["leadership", "decision_making", "mentorship"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "How do you recruit good engineers?",
     "role_tags": ["EM"], "competency_tags": ["leadership", "decision_making", "communication"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "Give an example of how you helped another employee grow.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "mentorship", "communication"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "Tell me about a time you had a conflict with your supervisor and how you resolved it.",
     "role_tags": ["EM"], "competency_tags": ["conflict_resolution", "communication", "adaptability"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "Tell me about a time when you had to deliver difficult feedback to an employee.",
     "role_tags": ["EM"], "competency_tags": ["communication", "conflict_resolution", "leadership", "failure_resilience"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "How do you build and maintain team morale?",
     "role_tags": ["EM"], "competency_tags": ["leadership", "communication", "adaptability"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "Tell me about a time when you had to advocate for your team to upper management.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "communication", "ownership", "decision_making"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "How do you handle attrition or losing key team members?",
     "role_tags": ["EM"], "competency_tags": ["leadership", "adaptability", "decision_making", "failure_resilience"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "Give an example of how you have fostered diversity and inclusion in your team.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "ownership", "communication"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "Describe how you manage remote or distributed teams.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "communication", "adaptability"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "How do you approach one-on-ones with your direct reports?",
     "role_tags": ["EM"], "competency_tags": ["leadership", "communication", "mentorship"], "difficulty": "standard", "level_band": "manager"},
]


# ---------------------------------------------------------------------------
# PDF Question Bank — EM-Specific Questions (Project & Technical)
# ---------------------------------------------------------------------------
PDF_EM_PROJ_QUESTIONS = [
    {"question_text": "As a manager, how do you handle trade-offs?",
     "role_tags": ["EM"], "competency_tags": ["decision_making", "leadership", "technical_challenge"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "Describe how you deal with change management.",
     "role_tags": ["EM"], "competency_tags": ["adaptability", "leadership", "communication"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "Describe in detail a project that failed.",
     "role_tags": ["EM"], "competency_tags": ["failure_resilience", "leadership", "problem_solving", "ownership"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "Describe a project in the past that was behind schedule. What concrete steps did you take to remedy the situation?",
     "role_tags": ["EM"], "competency_tags": ["problem_solving", "decision_making", "leadership", "adaptability"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "Tell me how you would balance engineering limitations with customer requirements.",
     "role_tags": ["EM"], "competency_tags": ["decision_making", "technical_challenge", "customer_obsession"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "What was the largest project you have executed?",
     "role_tags": ["EM"], "competency_tags": ["leadership", "decision_making", "ownership", "technical_challenge"], "difficulty": "advanced", "level_band": "manager"},

    {"question_text": "Tell me about a time you needed to deliver a project on a deadline but there were multiple roadblocks. How did you manage that?",
     "role_tags": ["EM"], "competency_tags": ["problem_solving", "adaptability", "leadership", "decision_making"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "Tell me about the most technically complex project you have managed. How did you resource your team?",
     "role_tags": ["EM"], "competency_tags": ["leadership", "technical_challenge", "decision_making", "ownership"], "difficulty": "advanced", "level_band": "manager"},

    {"question_text": "How do you deal with an engineer who is not being a team player?",
     "role_tags": ["EM"], "competency_tags": ["conflict_resolution", "leadership", "communication", "teamwork"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "Describe your approach to setting goals for your team.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "decision_making", "ownership"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "Describe a situation where you had to manage competing priorities across multiple projects.",
     "role_tags": ["EM"], "competency_tags": ["decision_making", "adaptability", "leadership"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "Tell me about a time when you had to make a decision with incomplete information.",
     "role_tags": ["EM"], "competency_tags": ["decision_making", "leadership", "failure_resilience"], "difficulty": "standard", "level_band": "manager"},

    {"question_text": "Describe a time when you had to align your team with broader organizational changes.",
     "role_tags": ["EM"], "competency_tags": ["leadership", "communication", "adaptability"], "difficulty": "standard", "level_band": "manager"},

    # --- EM customer_obsession gap fill ---
    # EM-CUST-01: Building customer-centric engineering culture
    {"question_text": "Tell me about a time you instilled a customer-first mindset in your engineering team. How did you make engineers care about user experience?",
     "role_tags": ["EM"], "competency_tags": ["customer_obsession", "leadership", "communication"], "difficulty": "standard", "level_band": "manager"},
    # EM-CUST-02: Using customer feedback to shape priorities
    {"question_text": "Describe a time when customer feedback fundamentally changed your team's engineering priorities. How did you translate user pain into technical action?",
     "role_tags": ["EM"], "competency_tags": ["customer_obsession", "decision_making", "leadership", "adaptability"], "difficulty": "advanced", "level_band": "manager"},
    # EM-CUST-03: Managing customer escalations
    {"question_text": "Tell me about a critical customer escalation your team handled. How did you balance the immediate fix with long-term reliability?",
     "role_tags": ["EM"], "competency_tags": ["customer_obsession", "problem_solving", "leadership", "failure_resilience"], "difficulty": "advanced", "level_band": "manager"},
    # EM-CUST-04: Connecting engineers to users
    {"question_text": "How have you connected your engineering team directly with customers or end users? What impact did that have on product quality?",
     "role_tags": ["EM"], "competency_tags": ["customer_obsession", "leadership", "communication", "innovation"], "difficulty": "standard", "level_band": "manager"},
    # EM-CUST-05: Advocating for customer needs vs. technical goals
    {"question_text": "Describe a situation where your team wanted to pursue a technical initiative but customer needs demanded something different. How did you navigate the tension?",
     "role_tags": ["EM"], "competency_tags": ["customer_obsession", "decision_making", "leadership", "conflict_resolution"], "difficulty": "advanced", "level_band": "manager"},
]

# fmt: on


# ---------------------------------------------------------------------------
# Seed logic
# ---------------------------------------------------------------------------
ALL_QUESTIONS = (
    LEGACY_QUESTIONS
    + PDF_CORE_QUESTIONS
    + PDF_MLE_QUESTIONS
    + PDF_PM_QUESTIONS
    + PDF_TPM_QUESTIONS
    + PDF_EM_PEOPLE_QUESTIONS
    + PDF_EM_PROJ_QUESTIONS
)


async def seed():
    """Truncate questions and re-seed all data."""
    await init_db()

    from sqlalchemy import text

    async with AsyncSessionLocal() as db:
        # Clear existing questions (CASCADE handles FK refs from mock_sessions)
        await db.execute(text("TRUNCATE questions CASCADE"))
        await db.commit()

    inserted = 0
    skipped = 0
    seen = set()  # Track (question_text, difficulty, level_band) for dedup

    async with AsyncSessionLocal() as db:
        for q_data in ALL_QUESTIONS:
            # Normalize competency tags
            tags = normalize_tags(q_data["competency_tags"])

            # Build dedup key
            key = (
                q_data["question_text"],
                q_data["difficulty"],
                q_data.get("level_band"),
            )

            if key in seen:
                skipped += 1
                continue
            seen.add(key)

            question = Question(
                question_text=q_data["question_text"],
                role_tags=q_data["role_tags"],
                competency_tags=tags,
                difficulty=q_data["difficulty"],
                level_band=q_data.get("level_band"),
                source="curated",
            )
            db.add(question)
            inserted += 1

        await db.commit()

    print(f"\n📝 Questions seeded: {inserted} inserted, {skipped} skipped (duplicates)")
    print(f"   Total in seed data: {len(ALL_QUESTIONS)}")

    # Print stats
    role_counts: dict[str, int] = {}
    level_counts: dict[str, int] = {}
    for q in ALL_QUESTIONS:
        key = (q["question_text"], q["difficulty"], q.get("level_band"))
        if key not in seen:
            continue  # Only count unique
        for role in q["role_tags"]:
            role_counts[role] = role_counts.get(role, 0) + 1
        lb = q.get("level_band", "none")
        level_counts[lb] = level_counts.get(lb, 0) + 1

    print("\n   Role coverage:")
    for role, count in sorted(role_counts.items()):
        print(f"   - {role}: {count}")

    print("\n   Level band coverage:")
    for lb, count in sorted(level_counts.items()):
        print(f"   - {lb}: {count}")


if __name__ == "__main__":
    asyncio.run(seed())
