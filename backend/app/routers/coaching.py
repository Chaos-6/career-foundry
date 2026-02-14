"""
Coaching endpoints — manage student/coach relationships and feedback.

Coach endpoints (requires auth):
  POST   /coaching/invite           — invite a student by email
  GET    /coaching/students         — list coach's students + summary stats
  GET    /coaching/students/{id}/evaluations — student's evaluation history
  PATCH  /evaluations/{id}/coach-notes      — add/update feedback on evaluation

Student endpoints (requires auth):
  GET    /coaching/invites          — list pending invites for the student
  POST   /coaching/invites/{id}/accept  — accept an invite
  POST   /coaching/invites/{id}/decline — decline an invite
  GET    /coaching/my-coaches       — list active coaches

Both:
  DELETE /coaching/relationships/{id} — remove a relationship (either party)
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import (
    Answer,
    AnswerVersion,
    CoachingRelationship,
    Evaluation,
    User,
)
from app.services.email import (
    coaching_accepted_email,
    coaching_invite_email,
    send_email,
)
from app.schemas.coaching import (
    CoachDashboardResponse,
    CoachingRelationshipResponse,
    CoachNotesRequest,
    CoachNotesResponse,
    InviteStudentRequest,
    StudentSummary,
)

router = APIRouter(prefix="/api/v1/coaching", tags=["coaching"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_relationship_response(
    rel: CoachingRelationship,
    coach: User,
    student: User,
) -> CoachingRelationshipResponse:
    """Map a DB relationship + both users into the response schema."""
    return CoachingRelationshipResponse(
        id=rel.id,
        coach_id=coach.id,
        coach_email=coach.email,
        coach_name=coach.display_name,
        student_id=student.id,
        student_email=student.email,
        student_name=student.display_name,
        status=rel.status,
        created_at=rel.created_at,
        accepted_at=rel.accepted_at,
    )


# ---------------------------------------------------------------------------
# Coach: Invite a student
# ---------------------------------------------------------------------------

@router.post("/invite", response_model=CoachingRelationshipResponse, status_code=201)
async def invite_student(
    request: InviteStudentRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Invite a student by email.

    If the student already has an account, links directly.
    If not, stores the invited email — when they register, we can
    auto-match pending invites.

    Prevents:
    - Self-invite
    - Duplicate active/pending invite for the same pair
    """
    if request.email == user.email:
        raise HTTPException(status_code=400, detail="You cannot invite yourself.")

    # Look up the student account (may not exist yet)
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    student = result.scalar_one_or_none()

    student_id = student.id if student else None

    # Check for existing relationship (if student exists)
    if student_id:
        existing = await db.execute(
            select(CoachingRelationship).where(
                CoachingRelationship.coach_id == user.id,
                CoachingRelationship.student_id == student_id,
                CoachingRelationship.status.in_(["pending", "active"]),
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="An invite or active relationship already exists with this student.",
            )

    rel = CoachingRelationship(
        coach_id=user.id,
        student_id=student_id,
        invited_email=request.email,
        status="pending",
    )
    db.add(rel)
    await db.commit()
    await db.refresh(rel)

    # Send coaching invite email (respects notification preferences)
    should_email = not student or getattr(student, "email_notifications", True)
    if should_email:
        subject, html = coaching_invite_email(user.display_name, user.email)
        background_tasks.add_task(send_email, request.email, subject, html)

    # Build response — student may be a placeholder if account doesn't exist
    return CoachingRelationshipResponse(
        id=rel.id,
        coach_id=user.id,
        coach_email=user.email,
        coach_name=user.display_name,
        student_id=student_id or UUID(int=0),
        student_email=request.email,
        student_name=student.display_name if student else None,
        status=rel.status,
        created_at=rel.created_at,
        accepted_at=rel.accepted_at,
    )


# ---------------------------------------------------------------------------
# Coach: Dashboard — list students with stats
# ---------------------------------------------------------------------------

@router.get("/students", response_model=CoachDashboardResponse)
async def get_coach_students(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all students linked to this coach with summary stats.

    Returns active students with their evaluation counts, averages,
    and latest activity dates. Also includes count of pending invites.
    """
    # Active relationships
    active_query = (
        select(CoachingRelationship, User)
        .join(User, CoachingRelationship.student_id == User.id)
        .where(
            CoachingRelationship.coach_id == user.id,
            CoachingRelationship.status == "active",
        )
        .order_by(User.display_name, User.email)
    )
    active_result = await db.execute(active_query)
    active_rows = active_result.all()

    # Pending invites count
    pending_result = await db.execute(
        select(func.count(CoachingRelationship.id)).where(
            CoachingRelationship.coach_id == user.id,
            CoachingRelationship.status == "pending",
        )
    )
    pending_count = pending_result.scalar() or 0

    # Build student summaries with stats
    students = []
    for rel, student in active_rows:
        # Get evaluation stats for this student
        eval_stats = await db.execute(
            select(
                func.count(Evaluation.id),
                func.avg(Evaluation.average_score),
                func.max(Evaluation.average_score),
                func.max(Evaluation.created_at),
            )
            .join(AnswerVersion, Evaluation.answer_version_id == AnswerVersion.id)
            .join(Answer, AnswerVersion.answer_id == Answer.id)
            .where(Answer.user_id == student.id, Evaluation.status == "completed")
        )
        row = eval_stats.one()

        students.append(
            StudentSummary(
                student_id=str(student.id),
                email=student.email,
                display_name=student.display_name,
                avatar_url=student.avatar_url,
                total_evaluations=row[0] or 0,
                average_score=round(float(row[1]), 1) if row[1] else None,
                best_score=round(float(row[2]), 1) if row[2] else None,
                latest_evaluation_date=(
                    row[3].isoformat() if row[3] else None
                ),
                relationship_id=str(rel.id),
            )
        )

    return CoachDashboardResponse(
        students=students,
        total_students=len(students),
        pending_invites=pending_count,
    )


# ---------------------------------------------------------------------------
# Coach: View a student's evaluations
# ---------------------------------------------------------------------------

@router.get("/students/{student_id}/evaluations")
async def get_student_evaluations(
    student_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a student's evaluation history (coach access only).

    Verifies an active coaching relationship exists before
    returning the student's data.
    """
    # Verify active coaching relationship
    rel_result = await db.execute(
        select(CoachingRelationship).where(
            CoachingRelationship.coach_id == user.id,
            CoachingRelationship.student_id == student_id,
            CoachingRelationship.status == "active",
        )
    )
    if not rel_result.scalar_one_or_none():
        raise HTTPException(
            status_code=403,
            detail="No active coaching relationship with this student.",
        )

    # Get student's evaluations with context
    from app.models import CompanyProfile, Question

    query = (
        select(
            Evaluation,
            AnswerVersion.version_number,
            Answer.id.label("answer_id"),
            Answer.target_role,
            Answer.custom_question_text,
            Answer.question_id,
            CompanyProfile.name.label("company_name"),
        )
        .join(AnswerVersion, Evaluation.answer_version_id == AnswerVersion.id)
        .join(Answer, AnswerVersion.answer_id == Answer.id)
        .join(CompanyProfile, Answer.target_company_id == CompanyProfile.id)
        .where(Answer.user_id == student_id, Evaluation.status == "completed")
        .order_by(Evaluation.created_at.desc())
        .limit(50)
    )
    result = await db.execute(query)
    rows = result.all()

    # Batch-load question texts
    question_ids = {r.question_id for r in rows if r.question_id}
    question_map: dict[str, str] = {}
    if question_ids:
        q_result = await db.execute(
            select(Question.id, Question.question_text).where(
                Question.id.in_(question_ids)
            )
        )
        question_map = {str(row.id): row.question_text for row in q_result.all()}

    evaluations = []
    for row in rows:
        ev: Evaluation = row[0]
        q_text = row.custom_question_text
        if not q_text and row.question_id:
            q_text = question_map.get(str(row.question_id))

        evaluations.append({
            "evaluation_id": str(ev.id),
            "answer_id": str(row.answer_id),
            "question_text": q_text,
            "company_name": row.company_name,
            "target_role": row.target_role,
            "average_score": round(float(ev.average_score), 1) if ev.average_score else None,
            "situation_score": ev.situation_score,
            "task_score": ev.task_score,
            "action_score": ev.action_score,
            "result_score": ev.result_score,
            "engagement_score": ev.engagement_score,
            "overall_score": ev.overall_score,
            "status": ev.status,
            "created_at": ev.created_at.isoformat(),
            "version_number": row.version_number,
            "coach_notes": ev.coach_notes,
        })

    return evaluations


# ---------------------------------------------------------------------------
# Coach: Add/update notes on a student's evaluation
# ---------------------------------------------------------------------------

@router.patch(
    "/evaluations/{evaluation_id}/coach-notes",
    response_model=CoachNotesResponse,
)
async def update_coach_notes(
    evaluation_id: UUID,
    request: CoachNotesRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add or update coach feedback on a student's evaluation.

    Verifies:
    1. The evaluation exists
    2. The coach has an active relationship with the evaluation's owner
    """
    # Load evaluation with answer chain to get the student
    ev_result = await db.execute(
        select(Evaluation, Answer.user_id)
        .join(AnswerVersion, Evaluation.answer_version_id == AnswerVersion.id)
        .join(Answer, AnswerVersion.answer_id == Answer.id)
        .where(Evaluation.id == evaluation_id)
    )
    ev_row = ev_result.one_or_none()
    if not ev_row:
        raise HTTPException(status_code=404, detail="Evaluation not found.")

    evaluation, student_id = ev_row

    # Verify coaching relationship
    rel_result = await db.execute(
        select(CoachingRelationship).where(
            CoachingRelationship.coach_id == user.id,
            CoachingRelationship.student_id == student_id,
            CoachingRelationship.status == "active",
        )
    )
    if not rel_result.scalar_one_or_none():
        raise HTTPException(
            status_code=403,
            detail="No active coaching relationship with this student.",
        )

    # Update coach notes
    evaluation.coach_notes = {
        "notes": request.notes,
        "focus_areas": request.focus_areas,
        "coach_id": str(user.id),
        "coach_name": user.display_name,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.commit()

    return CoachNotesResponse(
        notes=request.notes,
        focus_areas=request.focus_areas,
        coach_id=str(user.id),
        coach_name=user.display_name,
        updated_at=evaluation.coach_notes["updated_at"],
    )


# ---------------------------------------------------------------------------
# Student: List pending invites
# ---------------------------------------------------------------------------

@router.get("/invites", response_model=list[CoachingRelationshipResponse])
async def list_my_invites(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List pending coaching invites for the current student.

    Checks both by user_id (if already linked) and by email
    (for invites sent before the student registered).
    """
    query = (
        select(CoachingRelationship, User)
        .join(User, CoachingRelationship.coach_id == User.id)
        .where(
            CoachingRelationship.status == "pending",
            or_(
                CoachingRelationship.student_id == user.id,
                CoachingRelationship.invited_email == user.email,
            ),
        )
        .order_by(CoachingRelationship.created_at.desc())
    )
    result = await db.execute(query)
    rows = result.all()

    responses = []
    for rel, coach in rows:
        responses.append(
            CoachingRelationshipResponse(
                id=rel.id,
                coach_id=coach.id,
                coach_email=coach.email,
                coach_name=coach.display_name,
                student_id=user.id,
                student_email=user.email,
                student_name=user.display_name,
                status=rel.status,
                created_at=rel.created_at,
                accepted_at=rel.accepted_at,
            )
        )

    return responses


# ---------------------------------------------------------------------------
# Student: Accept an invite
# ---------------------------------------------------------------------------

@router.post("/invites/{invite_id}/accept", response_model=CoachingRelationshipResponse)
async def accept_invite(
    invite_id: UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept a pending coaching invite."""
    result = await db.execute(
        select(CoachingRelationship).where(CoachingRelationship.id == invite_id)
    )
    rel = result.scalar_one_or_none()

    if not rel:
        raise HTTPException(status_code=404, detail="Invite not found.")

    # Verify this invite is for the current user
    is_mine = (
        rel.student_id == user.id
        or rel.invited_email == user.email
    )
    if not is_mine or rel.status != "pending":
        raise HTTPException(status_code=400, detail="Cannot accept this invite.")

    # Update: set student_id (in case it was email-only invite), activate
    rel.student_id = user.id
    rel.status = "active"
    rel.accepted_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(rel)

    # Load coach for response
    coach_result = await db.execute(select(User).where(User.id == rel.coach_id))
    coach = coach_result.scalar_one()

    # Notify coach that student accepted
    if getattr(coach, "email_notifications", True):
        subject, html = coaching_accepted_email(user.display_name, user.email)
        background_tasks.add_task(send_email, coach.email, subject, html)

    return _build_relationship_response(rel, coach, user)


# ---------------------------------------------------------------------------
# Student: Decline an invite
# ---------------------------------------------------------------------------

@router.post("/invites/{invite_id}/decline")
async def decline_invite(
    invite_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Decline a pending coaching invite."""
    result = await db.execute(
        select(CoachingRelationship).where(CoachingRelationship.id == invite_id)
    )
    rel = result.scalar_one_or_none()

    if not rel:
        raise HTTPException(status_code=404, detail="Invite not found.")

    is_mine = (
        rel.student_id == user.id
        or rel.invited_email == user.email
    )
    if not is_mine or rel.status != "pending":
        raise HTTPException(status_code=400, detail="Cannot decline this invite.")

    rel.status = "revoked"
    await db.commit()

    return {"detail": "Invite declined."}


# ---------------------------------------------------------------------------
# Student: List my coaches
# ---------------------------------------------------------------------------

@router.get("/my-coaches", response_model=list[CoachingRelationshipResponse])
async def list_my_coaches(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List active coaches for the current user."""
    query = (
        select(CoachingRelationship, User)
        .join(User, CoachingRelationship.coach_id == User.id)
        .where(
            CoachingRelationship.student_id == user.id,
            CoachingRelationship.status == "active",
        )
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        _build_relationship_response(rel, coach, user)
        for rel, coach in rows
    ]


# ---------------------------------------------------------------------------
# Both: Remove a relationship
# ---------------------------------------------------------------------------

@router.delete("/relationships/{relationship_id}")
async def remove_relationship(
    relationship_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a coaching relationship (either party can do this)."""
    result = await db.execute(
        select(CoachingRelationship).where(
            CoachingRelationship.id == relationship_id
        )
    )
    rel = result.scalar_one_or_none()

    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found.")

    # Either coach or student can remove
    if rel.coach_id != user.id and rel.student_id != user.id:
        raise HTTPException(status_code=403, detail="Not your relationship.")

    rel.status = "revoked"
    await db.commit()

    return {"detail": "Relationship removed."}
