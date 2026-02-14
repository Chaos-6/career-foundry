"""
Gamification service — streaks and achievement badges.

Called after every completed evaluation to update the user's streak
and check for newly unlocked badges.

Streak logic (UTC-day based):
- Same day: no change (multiple evaluations per day don't double-count)
- Next day: increment streak
- Gap > 1 day: reset streak to 1

Badge definitions are hardcoded — no database table needed for 6 badges.
Each badge has an ID, display name, description, icon hint, and a
check function that returns True when the badge should be unlocked.
"""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Answer, AnswerVersion, CompanyProfile, Evaluation, MockSession, User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Badge definitions
# ---------------------------------------------------------------------------

BADGE_DEFINITIONS = [
    {
        "id": "first_evaluation",
        "name": "First Steps",
        "description": "Complete your first evaluation",
        "icon": "emoji_events",
    },
    {
        "id": "week_warrior",
        "name": "Week Warrior",
        "description": "Maintain a 7-day practice streak",
        "icon": "local_fire_department",
    },
    {
        "id": "perfect_score",
        "name": "Perfect Score",
        "description": "Score 5/5 on any dimension",
        "icon": "star",
    },
    {
        "id": "company_explorer",
        "name": "Company Explorer",
        "description": "Practice for 5+ different companies",
        "icon": "explore",
    },
    {
        "id": "revision_master",
        "name": "Revision Master",
        "description": "Improve your score on 3 revisions",
        "icon": "trending_up",
    },
    {
        "id": "mock_marathoner",
        "name": "Mock Marathoner",
        "description": "Complete 10 mock interviews",
        "icon": "timer",
    },
]


def _badge_ids(badges: list[dict]) -> set[str]:
    """Extract badge IDs from a user's badges JSONB array."""
    return {b["id"] for b in (badges or [])}


# ---------------------------------------------------------------------------
# Streak update
# ---------------------------------------------------------------------------

def update_streak(user: User) -> bool:
    """Update the user's practice streak based on today's date.

    Returns True if the streak changed (for logging), False if same-day.
    Uses UTC dates to avoid timezone ambiguity.
    """
    now = datetime.now(timezone.utc)
    today = now.date()

    last_date = None
    if user.last_practice_date:
        last_date = user.last_practice_date.date()

    if last_date == today:
        # Already practiced today — no change
        return False

    if last_date == today - timedelta(days=1):
        # Consecutive day — increment streak
        user.current_streak = (user.current_streak or 0) + 1
    else:
        # Gap (or first ever practice) — reset to 1
        user.current_streak = 1

    # Update longest streak if current exceeds it
    if (user.current_streak or 0) > (user.longest_streak or 0):
        user.longest_streak = user.current_streak

    user.last_practice_date = now
    return True


# ---------------------------------------------------------------------------
# Badge checks
# ---------------------------------------------------------------------------

async def check_and_award_badges(
    user: User,
    evaluation: Evaluation,
    db: AsyncSession,
) -> list[dict]:
    """Check all badge conditions and award any newly earned badges.

    Returns a list of newly unlocked badge dicts (for potential notifications).
    """
    existing_ids = _badge_ids(user.badges)
    newly_unlocked = []
    now = datetime.now(timezone.utc).isoformat()

    # --- First Evaluation ---
    if "first_evaluation" not in existing_ids:
        newly_unlocked.append({
            "id": "first_evaluation",
            "name": "First Steps",
            "unlocked_at": now,
        })

    # --- Week Warrior (7-day streak) ---
    if "week_warrior" not in existing_ids and (user.current_streak or 0) >= 7:
        newly_unlocked.append({
            "id": "week_warrior",
            "name": "Week Warrior",
            "unlocked_at": now,
        })

    # --- Perfect Score (any dimension = 5) ---
    if "perfect_score" not in existing_ids:
        scores = [
            evaluation.situation_score,
            evaluation.task_score,
            evaluation.action_score,
            evaluation.result_score,
            evaluation.engagement_score,
            evaluation.overall_score,
        ]
        if any(s == 5 for s in scores if s is not None):
            newly_unlocked.append({
                "id": "perfect_score",
                "name": "Perfect Score",
                "unlocked_at": now,
            })

    # --- Company Explorer (5+ different companies) ---
    if "company_explorer" not in existing_ids:
        company_count_result = await db.execute(
            select(func.count(func.distinct(Answer.target_company_id)))
            .where(Answer.user_id == user.id)
        )
        company_count = company_count_result.scalar() or 0
        if company_count >= 5:
            newly_unlocked.append({
                "id": "company_explorer",
                "name": "Company Explorer",
                "unlocked_at": now,
            })

    # --- Revision Master (improved score on 3 revisions) ---
    if "revision_master" not in existing_ids:
        # Find answers with 2+ versions where later version scored higher
        improved_count = 0

        # Get all user's answers with multiple versions
        multi_version_query = (
            select(Answer.id)
            .where(Answer.user_id == user.id, Answer.version_count >= 2)
        )
        mv_result = await db.execute(multi_version_query)
        answer_ids = [row[0] for row in mv_result.all()]

        for answer_id in answer_ids:
            # Get version scores ordered by version number
            version_scores_query = (
                select(
                    AnswerVersion.version_number,
                    func.max(Evaluation.average_score),
                )
                .join(Evaluation, Evaluation.answer_version_id == AnswerVersion.id)
                .where(
                    AnswerVersion.answer_id == answer_id,
                    Evaluation.status == "completed",
                )
                .group_by(AnswerVersion.version_number)
                .order_by(AnswerVersion.version_number)
            )
            vs_result = await db.execute(version_scores_query)
            scores = vs_result.all()

            # Check if any version improved over its predecessor
            for i in range(1, len(scores)):
                prev_score = scores[i - 1][1]
                curr_score = scores[i][1]
                if prev_score is not None and curr_score is not None:
                    if float(curr_score) > float(prev_score):
                        improved_count += 1
                        break  # One improvement per answer is enough

            if improved_count >= 3:
                break

        if improved_count >= 3:
            newly_unlocked.append({
                "id": "revision_master",
                "name": "Revision Master",
                "unlocked_at": now,
            })

    # --- Mock Marathoner (10 completed mock sessions) ---
    if "mock_marathoner" not in existing_ids:
        mock_count_result = await db.execute(
            select(func.count(MockSession.id))
            .where(MockSession.user_id == user.id, MockSession.completed == True)  # noqa: E712
        )
        mock_count = mock_count_result.scalar() or 0
        if mock_count >= 10:
            newly_unlocked.append({
                "id": "mock_marathoner",
                "name": "Mock Marathoner",
                "unlocked_at": now,
            })

    # Apply newly unlocked badges
    if newly_unlocked:
        current_badges = list(user.badges or [])
        current_badges.extend(newly_unlocked)
        user.badges = current_badges
        logger.info(
            f"User {user.id} unlocked {len(newly_unlocked)} badge(s): "
            f"{[b['id'] for b in newly_unlocked]}"
        )

    return newly_unlocked
