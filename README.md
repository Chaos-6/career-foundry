# Career Foundry

**AI-powered behavioral interview coaching for tech professionals.**

Career Foundry helps engineers, PMs, and technical leaders practice behavioral interviews with structured, AI-driven feedback. Paste a STAR-formatted answer, get scored on six dimensions with company-specific alignment — or try the Agentic AI Engineer track for 0-100 scoring with a Staff Engineer rewrite of your answer.

Built as a full-stack SaaS application: async Python backend, React 19 frontend, PostgreSQL, Claude AI evaluation pipeline, Stripe billing, OAuth, and Docker deployment.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  React 19 + TypeScript + MUI 6 + TanStack Query            │
│  14 pages · 12 shared components · Recharts visualizations  │
├─────────────────────────────────────────────────────────────┤
│  FastAPI (async) + SQLAlchemy 2.0 + Pydantic v2             │
│  13 routers · 59 API endpoints · 16 services                │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL 16 · 9 tables · JSONB · Alembic migrations      │
├─────────────────────────────────────────────────────────────┤
│  Claude AI (Anthropic SDK) · Background evaluation pipeline │
└─────────────────────────────────────────────────────────────┘
```

**~24,000 lines** of application code (Python + TypeScript), built across 25 incremental commits.

---

## Core Features

### Dual Evaluation Tracks

| | Standard (STAR) | Agentic AI Engineer |
|---|---|---|
| **Scoring** | 6 dimensions, 1-5 scale | 4 dimensions, 0-100 scale |
| **Output** | Markdown with parsed sections | Structured JSON with hiring decision |
| **Company Context** | Required (22+ profiles with principles) | Optional |
| **Interview Types** | Behavioral | Behavioral + System Design |
| **Hero Feature** | Company alignment analysis | "The Diff" — Staff Engineer rewrite |

The evaluation pipeline runs as a **FastAPI background task** with its own database session. It commits at each status transition (`queued -> analyzing -> completed`) so the frontend can poll progress in real time.

A **PromptFactory** (strategy pattern) routes to the correct system prompt, temperature, token budget, and output parser based on `InterviewRole` + `InterviewType` — the pipeline itself doesn't know prompt details.

### Evaluation Pipeline

```
POST /evaluations (201 Created, status=queued)
         │
         ▼  BackgroundTask
    Load answer + version + company
         │
         ▼
    PromptFactory.create(role, type, question, answer, ...)
         │
         ▼
    Claude API call (Anthropic SDK)
         │
         ├── Standard: regex parse scores → store in typed columns
         └── Agentic: JSON parse → store in JSONB columns
         │
         ▼
    Update best_score, streak, badges → commit
```

### Authentication & Authorization

- **JWT access tokens** (15 min) with refresh rotation (7 day)
- **Google and GitHub OAuth** via authorization code grant
- Automatic account linking when OAuth email matches existing account
- Tier enforcement: free (5 evals/month) vs. pro (unlimited)
- Role-based access: moderator flag gates the community moderation queue

### Monetization

- **Stripe Checkout** for subscription upgrades (Free → Pro)
- **Stripe Customer Portal** for billing management
- **Webhook handler** processes `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`
- Monthly counter reset script for evaluation quotas

### Coaching System

Full invite-based coaching workflow:
1. Coach invites student by email → `status: pending`
2. Student accepts → `status: active`
3. Coach views student's evaluation history and adds feedback
4. Email notifications at each stage (SMTP with dev-mode logging fallback)

### Additional Features

- **Gamification** — Practice streaks (consecutive days) and 6 achievement badges stored as JSONB
- **Mock Interview Mode** — Timed practice sessions with countdown
- **AI Answer Generator** — Claude generates STAR answers from bullet points
- **Answer Templates** — Save and reuse well-structured answer frameworks
- **Version Comparison** — Side-by-side revision diffs with score deltas
- **PDF Export** — Branded evaluation reports via ReportLab
- **Evaluation Sharing** — Public read-only links with unique share tokens
- **Bulk Import** — Parse `.txt`/`.md` files with `---` separators into answers
- **Inline Suggestions** — AI-powered improvement tips for weak dimensions (score <= 3)
- **Spaced Repetition** — Recommended questions based on time since last practice
- **Community Questions** — User submissions with moderation queue (approve/reject workflow)
- **Voice Input** — Web Speech API for answer dictation
- **Analytics Dashboard** — Score trends, dimension breakdown, company distribution charts

---

## Tech Stack

### Backend

| Layer | Technology |
|---|---|
| Framework | FastAPI (async) |
| ORM | SQLAlchemy 2.0 with async sessions (asyncpg driver) |
| Database | PostgreSQL 16 |
| Migrations | Alembic (async template) |
| Validation | Pydantic v2 with `from_attributes` mode |
| AI | Anthropic Claude SDK (claude-sonnet-4-20250514) |
| Auth | python-jose (JWT), passlib (bcrypt), OAuth 2.0 |
| Payments | Stripe SDK with webhook verification |
| PDF | ReportLab (Platypus flowable layout) |
| Email | smtplib with HTML templates |
| Rate Limiting | In-memory sliding window (middleware + per-route) |
| Testing | pytest + pytest-asyncio + httpx |

### Frontend

| Layer | Technology |
|---|---|
| Framework | React 19 |
| Language | TypeScript (strict) |
| UI Library | Material-UI (MUI) v6 |
| Routing | React Router v7 |
| Server State | TanStack React Query v5 |
| HTTP Client | Axios with interceptors (auto token refresh) |
| Charts | Recharts (radar, line, bar, pie) |
| Speech | Web Speech API |

### Infrastructure

| Layer | Technology |
|---|---|
| Containers | Docker + Docker Compose (3-service stack) |
| Database | PostgreSQL 16 Alpine with persistent volume |
| Backend | Uvicorn ASGI server |
| Frontend | Nginx serving React build |

---

## Data Model

```
CompanyProfile ─────┐
  22+ companies      │  1:N
  JSONB principles   │
                     ▼
Question ──────── Answer ──────── AnswerVersion ──────── Evaluation
  100+ questions   tracks:         revision history       standard: 6 scores (1-5)
  role/competency  standard │       v1, v2, v3...         agentic: JSONB (0-100)
  tags             agentic  │                              hiring_decision
                            │
User ───────────────────────┘
  JWT + OAuth         │
  streaks, badges     │  coaching_relationships
  plan_tier           │
                      ▼
              CoachingRelationship
                coach ↔ student

MockSession          AnswerTemplate
  timed practice      reusable STAR frameworks
```

9 tables with UUID primary keys, JSONB for flexible data (principles, tags, badges, agentic scores), and `server_default=func.now()` timestamps.

---

## API Surface

**59 endpoints** across 13 routers:

| Router | Endpoints | Highlights |
|---|---|---|
| Auth | 4 | Register, login, refresh, current user |
| OAuth | 4 | Google + GitHub authorization flows |
| Companies | 2 | Company profiles with guiding principles |
| Questions | 5 | Bank, random picker, community moderation |
| Answers | 5 | Create, revise, compare versions, bulk import |
| Evaluations | 7 | Create (async), poll, PDF export, share, suggestions |
| Dashboard | 5 | Stats, recent evals, score history, recommendations |
| Mock Interview | 2 | Timed sessions |
| Generator | 1 | AI answer generation |
| Coaching | 9 | Invite workflow, student evals, coach notes |
| Templates | 5 | CRUD + save-from-evaluation |
| Scenarios | 4 | Agentic question library (30 scenarios) |
| Billing | 4 | Stripe checkout, portal, webhooks |

Rate limiting: 100 req/min global (middleware) + 10 req/min on expensive endpoints (evaluations, generation).

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 16

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env: DATABASE_URL, ANTHROPIC_API_KEY, SECRET_KEY

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm start
# Opens at http://localhost:3000
```

### Docker (full stack)

```bash
docker compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

---

## Project Structure

```
backend/
  app/
    config.py              # Pydantic Settings (.env)
    database.py            # Async engine + session factory
    main.py                # FastAPI app, middleware, router registration
    models/                # 9 SQLAlchemy models
    schemas/               # Pydantic request/response schemas
    routers/               # 13 API routers (59 endpoints)
    services/              # 16 service modules
      evaluation_pipeline.py   # Background task orchestrator
      prompt_factory.py        # Strategy pattern for prompt routing
      prompts.py               # Standard STAR evaluation prompt
      prompts_agentic.py       # Agentic behavioral + system design prompts
      score_parser.py          # Regex parser for STAR scores
      gamification.py          # Streaks + badge engine
      pdf_report.py            # ReportLab PDF generation
      email.py                 # SMTP transactional emails
      suggestions.py           # AI inline improvement tips
      scenario_loader.py       # File-backed agentic scenarios
    data/
      scenarios.json           # 30 agentic interview scenarios
    dependencies.py            # Auth + rate limit dependencies
    rate_limit.py              # Sliding window middleware
  alembic/                 # Database migrations
  scripts/                 # Seed data, monthly reset
  tests/                   # pytest suite

frontend/
  src/
    api/client.ts          # 59 typed API functions + interceptors
    hooks/useAuth.tsx       # Auth state management
    theme/index.ts          # Navy/green design tokens, MUI overrides
    components/
      Layout.tsx               # App shell with grouped sidebar nav
      AgenticEvaluationView.tsx # Radar chart + hiring badge + "The Diff"
      ScoreBar.tsx             # Color-coded 1-5 score bars
    pages/
      Dashboard.tsx            # Hero stats, streaks, recent evals
      NewEvaluation.tsx        # Dual-track form with progress bar
      EvaluationDetail.tsx     # Results (standard or agentic)
      Analytics.tsx            # Score trends, dimension charts
      CoachDashboard.tsx       # Student management
      ... (14 pages total)
```

---

## Design Decisions

**Async-first backend.** Every database call uses `AsyncSession` with `asyncpg`. Evaluations run as background tasks with their own sessions — the API returns immediately with `status: queued` while Claude processes the answer.

**PromptFactory over if/else.** Adding a new interview type (e.g., product sense, case study) means adding one enum value and one builder function. The pipeline and routers don't change.

**JSONB for evolving schemas.** Agentic scores have different dimensions than STAR scores. Rather than widening the table for every new track, agentic results live in `JSONB` columns while STAR scores use typed `Integer` columns. Both coexist in the same `evaluations` table.

**File-backed scenarios.** The 30 agentic scenarios are stored in `scenarios.json`, not the database. They're curated content that changes with code deploys, not user-generated data. A JSON file is simpler to edit, review in PRs, and version control than DB rows.

**Nullable company for agentic.** Standard STAR evaluations are company-specific (aligned to Amazon's LPs, Netflix's Core Values, etc.). Agentic evaluations are role-specific — they don't need a company context. Rather than two separate `Answer` tables, `target_company_id` is nullable.

**Rate limiting without Redis.** The in-memory sliding window works for single-process deployment. When scaling to multiple workers, swap the storage backend to Redis — the interface stays the same.

---

## License

This project is proprietary. All rights reserved.
