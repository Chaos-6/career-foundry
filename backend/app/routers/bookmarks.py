"""
Question bookmark endpoints — save/unsave favorite questions.

Authenticated-only. Users can bookmark questions for quick access
from the Question Bank page.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Question, User, UserBookmark

router = APIRouter(prefix="/api/v1/questions", tags=["bookmarks"])


class BookmarkResponse(BaseModel):
    """Confirmation that a bookmark was created or already exists."""

    model_config = ConfigDict(from_attributes=True)

    question_id: UUID
    bookmarked: bool


class BookmarkedQuestionResponse(BaseModel):
    """A bookmarked question with its metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question_text: str
    role_tags: list[str]
    competency_tags: list[str]
    difficulty: str
    level_band: str | None = None
    source: str


@router.post("/{question_id}/bookmark", response_model=BookmarkResponse)
async def bookmark_question(
    question_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bookmark a question. Idempotent — re-bookmarking is a no-op."""
    # Verify question exists
    q_result = await db.execute(
        select(Question).where(Question.id == question_id)
    )
    if not q_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Question not found")

    # Check if already bookmarked
    existing = await db.execute(
        select(UserBookmark).where(
            UserBookmark.user_id == user.id,
            UserBookmark.question_id == question_id,
        )
    )
    if existing.scalar_one_or_none():
        return BookmarkResponse(question_id=question_id, bookmarked=True)

    bookmark = UserBookmark(user_id=user.id, question_id=question_id)
    db.add(bookmark)
    await db.commit()

    return BookmarkResponse(question_id=question_id, bookmarked=True)


@router.delete("/{question_id}/bookmark", status_code=204)
async def unbookmark_question(
    question_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a bookmark. Idempotent — unbookmarking a non-bookmarked question is a no-op."""
    await db.execute(
        delete(UserBookmark).where(
            UserBookmark.user_id == user.id,
            UserBookmark.question_id == question_id,
        )
    )
    await db.commit()


@router.get("/bookmarked", response_model=list[BookmarkedQuestionResponse])
async def get_bookmarked_questions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all questions bookmarked by the current user."""
    result = await db.execute(
        select(Question)
        .join(UserBookmark, UserBookmark.question_id == Question.id)
        .where(UserBookmark.user_id == user.id)
        .order_by(UserBookmark.created_at.desc())
    )
    questions = result.scalars().all()

    return [
        BookmarkedQuestionResponse(
            id=q.id,
            question_text=q.question_text,
            role_tags=q.role_tags or [],
            competency_tags=q.competency_tags or [],
            difficulty=q.difficulty or "standard",
            level_band=q.level_band,
            source=q.source or "curated",
        )
        for q in questions
    ]


@router.get("/bookmarked/ids", response_model=list[str])
async def get_bookmarked_question_ids(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get just the IDs of bookmarked questions — lightweight for badge rendering."""
    result = await db.execute(
        select(UserBookmark.question_id).where(UserBookmark.user_id == user.id)
    )
    return [str(row[0]) for row in result.all()]
