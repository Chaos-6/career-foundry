"""
Pytest fixtures for BIAE integration tests.

Key patterns:
- Real PostgreSQL (not SQLite) — JSONB, UUID, and ARRAY don't work in SQLite
- Session-scoped setup_db creates tables once per test run
- Each fixture gets its own AsyncSession for isolation
- httpx AsyncClient with ASGITransport = real HTTP calls to FastAPI
- Session-scoped teardown cleans up ALL test debris after the full suite runs

Why session-level cleanup instead of per-fixture teardown?
  Tests create data both through fixtures AND through API calls (e.g. auth
  tests POST to /auth/register, answer tests POST to /api/v1/answers).
  Per-fixture teardown can't catch API-created data, and FK cascading
  is fragile when multiple tests share the same fixture instances.
  Instead, we let tests run freely, then do a single sweep at the end.
"""

import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.config import settings
from app.database import AsyncSessionLocal, Base, engine
from app.main import app

# Disable rate limiting during tests — tests run many requests from the same IP
settings.RATE_LIMIT_ENABLED = False
from app.models import (
    Answer,
    AnswerVersion,
    CompanyProfile,
    Evaluation,
    Question,
    User,
)


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    """Create all tables once before the test session.

    After ALL tests complete, sweep any test-created records so the dev
    database stays clean. Deletes in reverse FK dependency order.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # ── Post-session cleanup ──
    # Delete all test debris in correct FK dependency order.
    # Pattern: "Test Corp" companies and "test_*@example.com" users are
    # the markers for test-created data.
    async with AsyncSessionLocal() as session:
        # 1. Mock sessions — delete ALL that reference test-created data.
        #    Mock sessions created during tests reference test questions
        #    (duplicates) and test companies. Safest to delete any mock session
        #    not tied to a "real" question (i.e. questions that are duplicates).
        await session.execute(text(
            "DELETE FROM mock_sessions WHERE "
            "question_id IN ("
            "  SELECT q.id FROM questions q WHERE EXISTS ("
            "    SELECT 1 FROM questions q2"
            "    WHERE q2.question_text = q.question_text"
            "    AND q2.created_at < q.created_at"
            "  )"
            ")"
        ))
        # 2. Evaluations tied to test answer versions
        await session.execute(text(
            "DELETE FROM evaluations WHERE answer_version_id IN ("
            "  SELECT av.id FROM answer_versions av"
            "  JOIN answers a ON av.answer_id = a.id"
            "  WHERE a.target_company_id IN ("
            "    SELECT id FROM company_profiles WHERE name LIKE 'Test Corp%'"
            "  )"
            ")"
        ))
        # 3. Answer versions tied to test answers
        await session.execute(text(
            "DELETE FROM answer_versions WHERE answer_id IN ("
            "  SELECT id FROM answers WHERE target_company_id IN ("
            "    SELECT id FROM company_profiles WHERE name LIKE 'Test Corp%'"
            "  )"
            ")"
        ))
        # 4. Answers tied to Test Corp companies
        await session.execute(text(
            "DELETE FROM answers WHERE target_company_id IN ("
            "  SELECT id FROM company_profiles WHERE name LIKE 'Test Corp%'"
            ")"
        ))
        # 5. Coaching relationships tied to test users
        await session.execute(text(
            "DELETE FROM coaching_relationships WHERE "
            "coach_id IN (SELECT id FROM users WHERE email LIKE 'test_%@example.com') "
            "OR student_id IN (SELECT id FROM users WHERE email LIKE 'test_%@example.com')"
        ))
        # 6. Test Corp companies
        await session.execute(text(
            "DELETE FROM company_profiles WHERE name LIKE 'Test Corp%'"
        ))
        # 7. Test users (created by auth tests via API)
        await session.execute(text(
            "DELETE FROM users WHERE email LIKE 'test_%@example.com'"
        ))
        # 7. Duplicate questions (keep originals, delete copies with same text)
        await session.execute(text(
            "DELETE FROM questions WHERE id IN ("
            "  SELECT q.id FROM questions q"
            "  WHERE EXISTS ("
            "    SELECT 1 FROM questions q2"
            "    WHERE q2.question_text = q.question_text"
            "    AND q2.created_at < q.created_at"
            "  )"
            ")"
        ))
        await session.commit()


@pytest_asyncio.fixture
async def client(setup_db):
    """HTTP test client that talks to the real FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_company(setup_db):
    """Create a test company profile."""
    company = CompanyProfile(
        id=uuid.uuid4(),
        name=f"Test Corp {uuid.uuid4().hex[:6]}",
        slug=f"test-corp-{uuid.uuid4().hex[:6]}",
        principle_type="Core Values",
        principles=[
            {"name": "Excellence", "description": "Strive for excellence in everything."},
            {"name": "Innovation", "description": "Innovate boldly and continuously."},
        ],
        interview_focus="Demonstrate excellence and innovation with specific examples.",
        interview_tips=["Use STAR format", "Quantify results"],
    )
    async with AsyncSessionLocal() as session:
        session.add(company)
        await session.commit()
        await session.refresh(company)
    return company


@pytest_asyncio.fixture
async def test_question(setup_db):
    """Create a test behavioral question."""
    question = Question(
        id=uuid.uuid4(),
        question_text="Tell me about a time you solved a difficult technical problem.",
        role_tags=["MLE", "TPM"],
        company_tags=["Amazon", "Google"],
        competency_tags=["technical_challenge", "problem_solving"],
        difficulty="standard",
        level_band="senior",
        source="curated",
    )
    async with AsyncSessionLocal() as session:
        session.add(question)
        await session.commit()
        await session.refresh(question)
    return question


@pytest_asyncio.fixture
async def test_user(setup_db):
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="not-a-real-hash",
        display_name="Test User",
    )
    async with AsyncSessionLocal() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user):
    """Generate a valid JWT Bearer token header for the test user.

    This fixture creates a real access token using the app's auth service,
    so it exercises the same code path as production. Avoids mocking.
    """
    from app.services.auth import create_access_token

    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_answer(test_company, test_question):
    """Create a test answer with one version."""
    answer = Answer(
        id=uuid.uuid4(),
        user_id=None,  # Pre-auth: no user required
        question_id=test_question.id,
        target_company_id=test_company.id,
        target_role="MLE",
        experience_level="senior",
        version_count=1,
    )
    async with AsyncSessionLocal() as session:
        session.add(answer)
        await session.commit()
        await session.refresh(answer)
    return answer


@pytest_asyncio.fixture
async def test_answer_version(test_answer):
    """Create a test answer version."""
    version = AnswerVersion(
        id=uuid.uuid4(),
        answer_id=test_answer.id,
        version_number=1,
        answer_text="Situation: At my previous company, we had a critical ML pipeline... "
                    "Task: I was responsible for debugging the failing model... "
                    "Action: I analyzed the data distribution shift... "
                    "Result: The model accuracy improved from 78% to 94%.",
        word_count=42,
    )
    async with AsyncSessionLocal() as session:
        session.add(version)
        await session.commit()
        await session.refresh(version)
    return version


@pytest_asyncio.fixture
async def test_evaluation(test_answer_version):
    """Create a completed test evaluation with mock scores."""
    evaluation = Evaluation(
        id=uuid.uuid4(),
        answer_version_id=test_answer_version.id,
        status="completed",
        situation_score=4,
        task_score=3,
        action_score=4,
        result_score=5,
        engagement_score=3,
        overall_score=4,
        average_score=3.8,
        evaluation_markdown="## Evaluation\n\nThis is a test evaluation.",
        evaluation_sections={"scored_assessment": "Test section content"},
        company_alignment={"aligned_principles": ["Excellence"]},
        follow_up_questions=[{"question": "Can you elaborate on the data shift?"}],
        model_used="claude-sonnet-4-20250514",
        input_tokens=3500,
        output_tokens=4200,
        processing_seconds=28,
    )
    async with AsyncSessionLocal() as session:
        session.add(evaluation)
        await session.commit()
        await session.refresh(evaluation)
    return evaluation
