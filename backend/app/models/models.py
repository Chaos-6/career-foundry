"""
SQLAlchemy models for the Behavioral Interview Answer Evaluator.

8 tables:
1. CompanyProfile        — 22+ companies with guiding principles (JSONB)
2. Question              — 100+ behavioral questions tagged by role/competency/difficulty
3. User                  — Accounts with auth and preferences
4. Answer                — Links a user's question attempt to a company/role context
5. AnswerVersion         — Revisions of an answer (v1, v2, ...) for improvement tracking
6. Evaluation            — Claude's scored evaluation of an answer version
7. MockSession           — Timed practice session metadata
8. CoachingRelationship  — Student↔coach links with invite workflow

Key patterns:
- UUID primary keys everywhere
- JSONB for flexible data (principles, tags, evaluation sections)
- server_default=func.now() for timestamps (set by DB, not Python)
- user_id is nullable on Answer to support pre-auth evaluation flow
"""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


# ---------------------------------------------------------------------------
# Company Profiles
# ---------------------------------------------------------------------------

class CompanyProfile(Base):
    """A company with its guiding principles for interview evaluation.

    The principles column stores a JSONB array like:
    [{"name": "Customer Obsession", "description": "Leaders start with..."}]

    This flexible schema accommodates companies with very different principle
    structures (Amazon has 16 LPs, Netflix has 4 Core Principles, etc.).
    """

    __tablename__ = "company_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    principle_type = Column(String(100), nullable=False)  # "Leadership Principles", "Core Values", etc.
    principles = Column(JSONB, nullable=False, default=list)  # [{name, description}]
    interview_focus = Column(Text, nullable=False)
    interview_tips = Column(JSONB, default=list)  # Additional coaching context
    logo_url = Column(String(500))
    last_verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    answers = relationship("Answer", back_populates="company")


# ---------------------------------------------------------------------------
# Question Bank
# ---------------------------------------------------------------------------

class Question(Base):
    """A behavioral interview question with metadata tags.

    Tags are stored as JSONB arrays for flexible querying:
    - role_tags: ["MLE", "PM", "TPM", "EM"]
    - company_tags: ["Amazon", "Meta"]
    - competency_tags: ["conflict", "leadership", "technical_challenge"]

    Community-submitted questions go through a moderation workflow:
    - status: pending → approved / rejected
    - Only "approved" questions appear in the public question bank
    - Curated (seeded) questions default to "approved" for backwards compatibility
    """

    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_text = Column(Text, nullable=False)
    role_tags = Column(JSONB, nullable=False, default=list)
    company_tags = Column(JSONB, default=list)
    competency_tags = Column(JSONB, nullable=False, default=list)
    difficulty = Column(String(20), nullable=False, default="standard")  # standard, advanced, senior_plus
    level_band = Column(String(20))  # entry, mid, senior, staff, manager
    source = Column(String(50), default="curated")  # curated, community, user_contributed
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # --- Moderation fields (community submissions) ---
    status = Column(String(20), default="approved")  # pending, approved, rejected
    submitted_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    moderation_notes = Column(Text)  # Reason for rejection
    moderated_at = Column(DateTime(timezone=True))


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class User(Base):
    """A registered user with auth credentials and preferences.

    Supports both email/password and OAuth authentication:
    - password_hash is nullable for OAuth-only users
    - oauth_provider / oauth_provider_id track the OAuth identity
    - A user can have both a password AND an OAuth link (e.g. registered
      with email, later linked Google)
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # nullable for OAuth-only users
    display_name = Column(String(255))
    avatar_url = Column(String(500))  # From OAuth provider profile picture

    # OAuth fields
    oauth_provider = Column(String(50))      # "google", "github", or None
    oauth_provider_id = Column(String(255))  # Provider's unique user ID

    # Preferences
    default_company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"))
    default_role = Column(String(50))
    default_experience_level = Column(String(50))
    evaluations_this_month = Column(Integer, default=0)
    plan_tier = Column(String(20), default="free")  # free, pro
    is_moderator = Column(Boolean, default=False)  # Can review community submissions
    email_notifications = Column(Boolean, default=True)  # Opt-out for email notifications
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)

    # Relationships
    answers = relationship("Answer", back_populates="user")
    mock_sessions = relationship("MockSession", back_populates="user")


# ---------------------------------------------------------------------------
# Answers & Versions
# ---------------------------------------------------------------------------

class Answer(Base):
    """A user's answer attempt for a specific question + company/role context.

    Each answer can have multiple versions (revisions). The user_id is nullable
    to support the evaluation flow before authentication is built.
    """

    __tablename__ = "answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True)
    custom_question_text = Column(Text)  # If user typed a custom question
    target_company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    target_role = Column(String(50), nullable=False)
    experience_level = Column(String(50), nullable=False)
    version_count = Column(Integer, default=1)
    best_average_score = Column(Numeric(2, 1))  # Best avg across all versions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="answers")
    company = relationship("CompanyProfile", back_populates="answers")
    question = relationship("Question")
    versions = relationship("AnswerVersion", back_populates="answer", order_by="AnswerVersion.version_number")


class AnswerVersion(Base):
    """A specific revision of an answer.

    Version 1 is the original. Each subsequent version is a revision
    after the user reads feedback and improves their answer.
    """

    __tablename__ = "answer_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    answer_id = Column(UUID(as_uuid=True), ForeignKey("answers.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    answer_text = Column(Text, nullable=False)
    word_count = Column(Integer)
    is_ai_assisted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("answer_id", "version_number", name="uq_answer_version"),
    )

    # Relationships
    answer = relationship("Answer", back_populates="versions")
    evaluations = relationship("Evaluation", back_populates="answer_version")


# ---------------------------------------------------------------------------
# Evaluations
# ---------------------------------------------------------------------------

class Evaluation(Base):
    """Claude's scored evaluation of an answer version.

    Stores both the raw markdown and extracted structured data:
    - 6 dimension scores (1-5 each)
    - Parsed sections for programmatic access
    - Company alignment details
    - Predicted follow-up questions
    """

    __tablename__ = "evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    answer_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("answer_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(String(50), default="queued")  # queued, analyzing, completed, failed

    # Individual dimension scores (1-5)
    situation_score = Column(Integer)
    task_score = Column(Integer)
    action_score = Column(Integer)
    result_score = Column(Integer)
    engagement_score = Column(Integer)
    overall_score = Column(Integer)
    average_score = Column(Numeric(2, 1))

    # Full evaluation content
    evaluation_markdown = Column(Text)
    evaluation_sections = Column(JSONB)  # Parsed sections for structured access

    # Company alignment
    company_alignment = Column(JSONB)  # {aligned_principles: [], reinforce: []}

    # Follow-up questions
    follow_up_questions = Column(JSONB)  # [{question, why_asked, how_to_prepare}]

    # Coach feedback
    coach_notes = Column(JSONB)  # {notes: str, focus_areas: [str], coach_id: str}

    # Sharing — nullable UUID token; set when user shares the evaluation
    share_token = Column(UUID(as_uuid=True), unique=True, nullable=True, index=True)
    shared_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    model_used = Column(String(100))
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    processing_seconds = Column(Integer)
    error_message = Column(Text)  # Populated on failure
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    answer_version = relationship("AnswerVersion", back_populates="evaluations")


# ---------------------------------------------------------------------------
# Mock Interview Sessions
# ---------------------------------------------------------------------------

class MockSession(Base):
    """A timed practice session where the user answers under time pressure."""

    __tablename__ = "mock_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"))
    time_limit_seconds = Column(Integer, nullable=False)
    time_used_seconds = Column(Integer)
    answer_version_id = Column(UUID(as_uuid=True), ForeignKey("answer_versions.id"))
    evaluation_id = Column(UUID(as_uuid=True), ForeignKey("evaluations.id"))
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="mock_sessions")
    question = relationship("Question")
    answer_version = relationship("AnswerVersion")
    evaluation = relationship("Evaluation")


# ---------------------------------------------------------------------------
# Coaching Relationships
# ---------------------------------------------------------------------------

class CoachingRelationship(Base):
    """A student↔coach link with invite workflow.

    Lifecycle:
    - Coach invites student by email → status='pending'
    - Student accepts → status='active'
    - Either party can revoke → status='revoked'

    A student can have multiple coaches, and a coach can have multiple
    students. The unique constraint prevents duplicate active relationships.
    """

    __tablename__ = "coaching_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coach_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(20), default="pending")  # pending, active, revoked
    invited_email = Column(String(255))  # Email used in invite (student may not exist yet)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("coach_id", "student_id", name="uq_coaching_pair"),
    )

    # Relationships
    coach = relationship("User", foreign_keys=[coach_id])
    student = relationship("User", foreign_keys=[student_id])
