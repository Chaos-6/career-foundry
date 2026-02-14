# BIAE — Product Requirements Document

**Behavioral Interview Answer Evaluator**
**Version:** 3.0 — Phase 3 Planning
**Last Updated:** 2026-02-13
**Status:** Phase 1–2 Complete · Phase 3 In Planning

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Architecture](#2-architecture)
3. [Phase 1 — Foundation (Complete)](#3-phase-1--foundation-complete)
4. [Phase 2 — Growth Features (Complete)](#4-phase-2--growth-features-complete)
5. [Phase 3 — Production Hardening (Planned)](#5-phase-3--production-hardening-planned)
6. [Data Model](#6-data-model)
7. [API Reference](#7-api-reference)
8. [Frontend Pages & Components](#8-frontend-pages--components)
9. [AI Evaluation System](#9-ai-evaluation-system)
10. [Authentication & Authorization](#10-authentication--authorization)
11. [Monetization](#11-monetization)
12. [Configuration & Deployment](#12-configuration--deployment)

---

## 1. Product Overview

### What Is BIAE?

BIAE is an AI-powered coaching tool that helps tech job seekers practice and improve their behavioral interview answers. Users write STAR-formatted responses (Situation, Task, Action, Result), and Claude evaluates them across six dimensions with company-specific alignment analysis.

### Target Users

- Software engineers, PMs, TPMs, and EMs preparing for FAANG/tech behavioral interviews
- Career coaches managing multiple students
- Anyone who wants structured feedback on their storytelling for interviews

### Core Value Proposition

1. **Structured scoring** — 6-dimension rubric (1–5 scale) with actionable feedback
2. **Company-specific alignment** — 20+ company profiles with researched guiding principles
3. **Improvement tracking** — Version history, score trends, and readiness metrics
4. **Practice modes** — Timed mock interviews, AI-assisted answer generation, question bank

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, TypeScript, MUI 6, React Query 5, React Router 7, Recharts 3 |
| **Backend** | FastAPI, Python 3.10+, async SQLAlchemy 2.0, asyncpg |
| **Database** | PostgreSQL 13+ |
| **AI** | Claude (Anthropic SDK) — claude-sonnet-4-20250514 |
| **Auth** | JWT (python-jose + bcrypt), Google/GitHub OAuth |
| **Payments** | Stripe Checkout Sessions + Customer Portal |
| **PDF** | ReportLab + Pillow |

---

## 2. Architecture

### System Diagram

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend (React 19 + TypeScript)                            │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────┐   │
│  │ MUI 6   │ │React     │ │React     │ │ Recharts 3      │   │
│  │ UI Layer│ │Query 5   │ │Router 7  │ │ (Charts/Graphs) │   │
│  └────┬────┘ └────┬─────┘ └────┬─────┘ └────────┬────────┘   │
│       └───────────┼────────────┼─────────────────┘           │
│                   │ Axios + JWT Interceptors                 │
└───────────────────┼──────────────────────────────────────────┘
                    │ HTTPS
┌───────────────────┼──────────────────────────────────────────┐
│  Backend (FastAPI)│                                          │
│  ┌────────────────▼──────────────────────────────────────┐   │
│  │  11 Routers (auth, oauth, companies, questions,       │   │
│  │  answers, evaluations, dashboard, mock, generator,    │   │
│  │  billing, coaching)                                   │   │
│  └────────┬───────────────────────┬──────────────────────┘   │
│  ┌────────▼────────┐    ┌────────▼────────┐                  │
│  │ 8 Services      │    │ Dependencies    │                  │
│  │ (Claude, PDF,   │    │ (JWT auth,      │                  │
│  │  scoring, auth) │    │  DB sessions)   │                  │
│  └────────┬────────┘    └────────┬────────┘                  │
│           │                      │                           │
│  ┌────────▼──────────────────────▼────────┐                  │
│  │  SQLAlchemy 2.0 (Async) — 8 Models     │                  │
│  └────────────────────┬───────────────────┘                  │
└───────────────────────┼──────────────────────────────────────┘
                        │
            ┌───────────▼───────────┐
            │  PostgreSQL           │
            │  8 tables             │
            └───────────────────────┘
```

### Request Flow

```
User Action → React Component → API Client (Axios)
  → JWT attached via interceptor
  → FastAPI Router → Dependency Injection (auth + DB session)
  → Service Layer → Database / Claude API
  → Pydantic Response Schema → JSON → React Query Cache → UI
```

### Evaluation Pipeline (Background Task)

```
POST /evaluations → tier limit check → create Evaluation (status=queued)
  → BackgroundTask: run_evaluation_pipeline()
    → status=analyzing (commit, frontend can poll)
    → Claude API call (STARAnalysisService)
    → Parse scores, sections, alignment, follow-ups
    → status=completed (commit)
    → Update answer.best_average_score
    → Increment user.evaluations_this_month
```

---

## 3. Phase 1 — Foundation (Complete)

### Milestone 1–10: Core Application

**Commit:** `8dcb134` — Full-stack behavioral interview evaluator

**What was built:**
- FastAPI backend with async SQLAlchemy + PostgreSQL
- 250+ curated behavioral questions with role/competency/difficulty tags
- 20+ company profiles with researched guiding principles
- Answer CRUD with immutable version history
- Claude-powered 6-dimension STAR evaluation pipeline
- Score parsing from Claude's markdown output
- PDF report generation (ReportLab)
- Mock interview mode with countdown timer
- AI answer generator (bullet points → polished narrative)
- JWT authentication (register/login/refresh)

### Auth UI + Revision Flow

**Commit:** `b7a1b05`

- Login/Register page with tab switching
- ProtectedRoute component for auth-gated pages
- Inline revision editor on evaluation detail
- Side-by-side version score comparison page

### Enhanced Dashboard

**Commit:** `24de374`

- Personalized stats bar (total evals, avg score, best score, this month)
- Score trend area chart (Recharts, 30 days, 6 dimensions)
- Recent evaluations table (8 most recent)

### Advanced Analytics

**Commit:** `d995323`

- Competency radar chart (6 STAR dimensions)
- Interview readiness gauge (weighted: 40% score quality, 30% consistency, 30% trend)
- Per-company breakdown table
- Dimension breakdown horizontal bar chart

### Google & GitHub OAuth

**Commit:** `7a422af`

- Authorization Code flow for both providers
- Auto-account linking by email (existing password accounts)
- OAuth profile mapping (avatar, display name)
- Token delivery via URL fragment (security best practice)

### Stripe Monetization

**Commit:** `30fc1e1`

- Free tier: 5 evaluations/month
- Pro tier: $12/month, unlimited evaluations
- Stripe Checkout Sessions (hosted payment page, zero PCI burden)
- Webhook-based subscription fulfillment
- Stripe Customer Portal for subscription management
- UpgradePrompt dialog when free users hit their limit

---

## 4. Phase 2 — Growth Features (Complete)

### Community Question Submissions

**Commit:** `c2390be`

- Authenticated users can submit questions (min 20 chars, optional tags)
- Submissions enter moderation queue (status=pending)
- Moderator-only ModerationQueue page
- Approve (one-click) or reject (requires reason)
- Community badge on approved questions
- `is_moderator` role on User model

### Coaching Relationships

**Commit:** `cae8a98`

- CoachingRelationship junction table (coach_id, student_id, status)
- Email-based invite workflow (supports inviting unregistered users)
- Coach dashboard: student roster with stats (evals, avg score, best, last active)
- Expandable student detail with evaluation history
- Coach notes (JSONB) on individual evaluations
- Student view: pending invites, active coaches, accept/decline
- Either party can remove relationship

### Voice Input

**Commit:** `efe2ecc`

- VoiceInput component using Web Speech API (Chrome/Edge)
- Continuous listening with interim results display
- Integrated in NewEvaluation and MockInterview answer areas
- Appends transcribed text (doesn't replace)
- Auto-hides on unsupported browsers

### Mobile Optimization

**Commit:** `870ba25`

- Responsive h4 headings (1.5rem on mobile, 2.125rem on desktop)
- AppBar title: "BIAE" on mobile, full name on desktop
- Reduced content padding on mobile (16px vs 24px)
- Dashboard table: hides Company/Role/Status/Date on mobile
- Analytics company table: horizontal scroll with minWidth
- EvaluationDetail: buttons stack vertically on mobile
- QuestionBank: action buttons wrap with flexWrap + useFlexGap
- MockInterview: timer bar hides context info on mobile

---

## 5. Phase 3 — Production Hardening (Planned)

### P3.1 — Error Boundaries

**Goal:** Prevent white-screen crashes from bubbling up to the entire app.

**Scope:**
- Add React error boundary wrapper around each route in App.tsx
- Friendly error UI with "Refresh Page" and "Go to Dashboard" actions
- Log errors to console (future: send to error reporting service)
- Existing ErrorBoundary component in codebase — wire it into the route tree

**Files:** App.tsx, ErrorBoundary.tsx (may need enhancement)

### P3.2 — Loading & Empty State Polish

**Goal:** Consistent, polished loading skeletons and empty states across all pages.

**Scope:**
- Audit all pages for missing loading states
- Add skeleton placeholders matching final layout shape
- Consistent empty state pattern: icon + message + CTA button
- Error recovery: "Try Again" buttons that refetch data
- Evaluation polling: improve queued/analyzing states with progress steps

**Files:** All page components

### P3.3 — Rate Limiting

**Goal:** Protect the Claude API evaluation endpoint from abuse.

**Scope:**
- Add slowapi or custom middleware for per-IP and per-user rate limiting
- Evaluation endpoint: 10 requests/minute per user, 3/minute for anonymous
- Generator endpoint: 5 requests/minute per user
- Auth endpoints: 5 login attempts/minute per IP (brute force protection)
- Return 429 Too Many Requests with Retry-After header
- Frontend: handle 429 responses with user-friendly message

**Files:** main.py (middleware), evaluations.py, generator.py, auth.py, new frontend error handler

### P3.4 — Docker + Docker Compose

**Goal:** One-command local development and deployment-ready containerization.

**Scope:**
- `Dockerfile` for backend (Python 3.11, uvicorn)
- `Dockerfile` for frontend (Node 20, nginx for production)
- `docker-compose.yml` orchestrating:
  - PostgreSQL 15 (with health check)
  - Backend (depends_on postgres)
  - Frontend (depends_on backend)
- `.env.example` with all required variables documented
- `scripts/init-db.sh` for first-time database setup
- Volume mounts for persistent data

**Files:** Dockerfile (backend), Dockerfile (frontend), docker-compose.yml, .env.example, scripts/

### P3.5 — Frontend Tests

**Goal:** Test coverage for critical user flows using React Testing Library.

**Scope:**
- Test infrastructure: Jest + React Testing Library (already in package.json)
- Mock API client for all tests (MSW or manual mocks)
- Test files to create:
  - `Layout.test.tsx` — navigation rendering, mobile drawer toggle, auth state display
  - `Dashboard.test.tsx` — feature cards render, stats display, loading states
  - `NewEvaluation.test.tsx` — form validation, company/role selection, submit flow
  - `EvaluationDetail.test.tsx` — polling behavior, score display, revision flow
  - `MockInterview.test.tsx` — timer countdown, auto-submit, phase transitions
  - `QuestionBank.test.tsx` — filter state, search, question card rendering
  - `LoginPage.test.tsx` — tab switching, form validation, OAuth button rendering
  - `useAuth.test.tsx` — login/logout state, token management, hydration
  - `UpgradePrompt.test.tsx` — tier limit detection, dialog display
  - `VoiceInput.test.tsx` — browser support detection, callback firing
- Target: Cover the happy path for each critical flow + key error cases

**Files:** `frontend/src/__tests__/` or colocated `*.test.tsx` files

### P3.6 — Export & Sharing

**Goal:** Let users share evaluation results via public link.

**Scope:**
- New `share_token` column on Evaluation (UUID, nullable, indexed)
- `POST /api/v1/evaluations/{id}/share` — generates share_token, returns public URL
- `GET /api/v1/evaluations/shared/{token}` — public endpoint, no auth, read-only
- `DELETE /api/v1/evaluations/{id}/share` — revokes sharing
- Frontend: "Share" button on EvaluationDetail, copy-to-clipboard
- Shared view page: read-only evaluation with scores, markdown, company alignment
- No user info exposed on shared view (privacy)

**Files:** Evaluation model, evaluations.py router, new SharedEvaluation page, client.ts

### P3.7 — Notification System

**Goal:** Email notifications for coaching invites and moderation approvals.

**Scope:**
- Email service abstraction (start with SMTP, swap to SendGrid/SES later)
- Notification triggers:
  - Coaching invite sent → email to student
  - Coaching invite accepted → email to coach
  - Community question approved → email to submitter
  - Community question rejected → email to submitter (with reason)
- Email templates: simple HTML with inline styles (no build tool dependency)
- Configuration: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, FROM_EMAIL env vars
- Notification preferences: `email_notifications` boolean on User model (opt-out)

**Files:** New services/email.py, coaching.py router (triggers), questions.py router (triggers), User model update

### P3.8 — Answer Templates

**Goal:** Let users save and reuse STAR answer frameworks.

**Scope:**
- New `answer_templates` table: id, user_id, name, template_text, role_tags, competency_tags, created_at, updated_at
- CRUD endpoints: POST/GET/PUT/DELETE under `/api/v1/templates`
- Template selection in NewEvaluation: dropdown to load template into answer textarea
- Template creation from existing answers: "Save as Template" on EvaluationDetail
- Template library page (or section within existing page)

**Files:** New model, new router, new schemas, NewEvaluation.tsx update, client.ts

### P3.9 — Practice Streaks & Gamification

**Goal:** Encourage consistent practice with streaks and achievement badges.

**Scope:**
- New `practice_streaks` table: user_id, current_streak, longest_streak, last_practice_date
- Streak logic: increments on any evaluation completion, resets after 1 missed day
- Achievement badges (stored as JSONB on User or separate table):
  - "First Evaluation" — complete 1 evaluation
  - "Week Warrior" — 7-day streak
  - "Perfect Score" — any dimension scored 5/5
  - "Company Explorer" — evaluate for 5+ different companies
  - "Revision Master" — improve score on 3 revisions
  - "Mock Marathoner" — complete 10 mock interviews
- Dashboard widget: current streak + next badge progress
- Badge display on user profile/dashboard

**Files:** New model, dashboard.py updates, Dashboard.tsx widget, new badges component

### P3.10 — Spaced Repetition

**Goal:** Resurface weak-scoring questions for targeted practice.

**Scope:**
- Algorithm: questions where user scored ≤3 average, weighted by recency (older = more likely to appear)
- New endpoint: `GET /api/v1/questions/recommended` — returns prioritized practice list
- Integration: "Recommended for You" section on Dashboard (authenticated)
- "Practice Again" button linking to NewEvaluation with question pre-selected
- Tracks which questions have been practiced (uses existing evaluation data)

**Files:** questions.py router (new endpoint), Dashboard.tsx (new section), client.ts

### P3.11 — AI-Powered Inline Suggestions

**Goal:** Provide targeted improvement suggestions for specific STAR sections.

**Scope:**
- New endpoint: `POST /api/v1/evaluations/{id}/suggestions` — generates section-specific improvement tips
- Uses existing evaluation + answer text as context
- Returns structured suggestions: `{section: "situation", suggestion: "...", example: "..."}`
- Frontend: collapsible "How to Improve" cards under each dimension score
- Uses Claude with lower token budget (max_tokens=1000) for cost efficiency
- Only available for completed evaluations with scores ≤3 in any dimension

**Files:** evaluations.py router, new prompt template, EvaluationDetail.tsx, client.ts

### P3.12 — Bulk Import

**Goal:** Let users upload answers from text files or Google Docs.

**Scope:**
- File upload endpoint: `POST /api/v1/answers/import` — accepts .txt or .md files
- Parse format: expects STAR sections separated by headers (## Situation, ## Task, etc.)
- Batch creation: creates Answer + AnswerVersion for each parsed answer
- Import UI: drag-and-drop zone on NewEvaluation page
- Validation: minimum word count per section, max file size (100KB)
- Import summary: shows count of successfully parsed answers

**Files:** New import service, answers.py router update, NewEvaluation.tsx, client.ts

---

## 6. Data Model

### Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│  CompanyProfile  │       │    Question      │
│─────────────────│       │─────────────────│
│ id (PK)         │       │ id (PK)         │
│ name            │       │ question_text    │
│ slug            │       │ role_tags (JSON) │
│ principle_type  │       │ company_tags     │
│ principles (JSON)│      │ competency_tags  │
│ interview_focus │       │ difficulty       │
│ interview_tips  │       │ level_band       │
│ logo_url        │       │ source           │
│ last_verified_at│       │ status           │
│ created_at      │       │ submitted_by_id  │◄── User (FK)
│ updated_at      │       │ moderation_notes │
└────────┬────────┘       │ created_at       │
         │                └────────┬─────────┘
         │                         │
         │    ┌────────────────────┤
         │    │                    │
    ┌────▼────▼───┐     ┌─────────▼────────┐
    │   Answer     │     │  MockSession     │
    │──────────────│     │──────────────────│
    │ id (PK)      │     │ id (PK)          │
    │ user_id (FK) │◄──┐ │ user_id (FK)     │◄── User (FK)
    │ question_id  │   │ │ question_id (FK) │
    │ custom_q_text│   │ │ time_limit_secs  │
    │ company_id   │   │ │ time_used_secs   │
    │ target_role  │   │ │ answer_version_id│
    │ exp_level    │   │ │ evaluation_id    │
    │ version_count│   │ │ completed        │
    │ best_avg     │   │ │ created_at       │
    │ created_at   │   │ └──────────────────┘
    │ updated_at   │   │
    └──────┬───────┘   │
           │           │
    ┌──────▼───────┐   │  ┌───────────────────┐
    │ AnswerVersion│   │  │       User         │
    │──────────────│   │  │───────────────────│
    │ id (PK)      │   │  │ id (PK)            │
    │ answer_id(FK)│   └──│ email (unique)     │
    │ version_num  │      │ password_hash      │
    │ answer_text  │      │ display_name       │
    │ word_count   │      │ avatar_url         │
    │ is_ai_assist │      │ oauth_provider     │
    │ created_at   │      │ oauth_provider_id  │
    └──────┬───────┘      │ default_company_id │
           │              │ default_role       │
    ┌──────▼───────┐      │ default_exp_level  │
    │  Evaluation  │      │ evals_this_month   │
    │──────────────│      │ plan_tier          │
    │ id (PK)      │      │ is_moderator       │
    │ version_id   │      │ is_active          │
    │ status       │      │ created_at         │
    │ situation    │      │ last_login         │
    │ task         │      └────────┬───────────┘
    │ action       │               │
    │ result       │               │
    │ engagement   │      ┌────────▼───────────────┐
    │ overall      │      │ CoachingRelationship   │
    │ average      │      │────────────────────────│
    │ eval_markdown│      │ id (PK)                │
    │ eval_sections│      │ coach_id (FK → User)   │
    │ company_align│      │ student_id (FK → User) │
    │ follow_ups   │      │ status                 │
    │ coach_notes  │      │ invited_email          │
    │ model_used   │      │ created_at             │
    │ tokens (in/out)│    │ accepted_at            │
    │ proc_seconds │      │ UNIQUE(coach, student) │
    │ error_message│      └────────────────────────┘
    │ created_at   │
    └──────────────┘
```

### Table Summary

| Table | Rows (seed) | Purpose |
|-------|-------------|---------|
| company_profiles | 20+ | Company names, principles, interview guidance |
| questions | 250+ | Behavioral questions with tags and difficulty |
| users | — | User accounts (email/OAuth, preferences, tier) |
| answers | — | User answers linking question + company + role |
| answer_versions | — | Immutable revision history of answers |
| evaluations | — | Claude's scored assessments per version |
| mock_sessions | — | Timed practice session metadata |
| coaching_relationships | — | Coach↔student links with invite workflow |

---

## 7. API Reference

### Authentication

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | — | Create account, returns JWT pair |
| POST | `/auth/login` | — | Email/password login |
| POST | `/auth/refresh` | — | Exchange refresh token |
| GET | `/auth/me` | Required | Current user profile |
| GET | `/auth/oauth/google` | — | Redirect to Google OAuth |
| GET | `/auth/oauth/google/callback` | — | Google callback handler |
| GET | `/auth/oauth/github` | — | Redirect to GitHub OAuth |
| GET | `/auth/oauth/github/callback` | — | GitHub callback handler |

### Companies

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/companies` | — | List all companies (compact) |
| GET | `/api/v1/companies/{id}` | — | Full company profile with principles |

### Questions

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/questions` | — | List/filter/search questions |
| GET | `/api/v1/questions/random` | — | Random question (with optional filters) |
| POST | `/api/v1/questions` | Required | Submit community question |
| GET | `/api/v1/questions/moderation/pending` | Moderator | Pending submissions queue |
| PATCH | `/api/v1/questions/{id}/moderation` | Moderator | Approve or reject |

### Answers

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/answers` | Optional | Create answer + first version |
| GET | `/api/v1/answers/{id}` | — | Answer with all versions |
| POST | `/api/v1/answers/{id}/versions` | — | Add revision |
| GET | `/api/v1/answers/{id}/compare` | — | Versions with scores for comparison |

### Evaluations

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/evaluations` | Required | Create evaluation (background task) |
| GET | `/api/v1/evaluations/{id}` | — | Status + results (poll until complete) |
| GET | `/api/v1/evaluations/{id}/report/pdf` | — | Download PDF report |

### Dashboard & Analytics

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/dashboard/stats` | Required | Summary stats |
| GET | `/api/v1/dashboard/recent` | Required | Recent evaluations |
| GET | `/api/v1/dashboard/score-history` | Required | Score data for trend chart |
| GET | `/api/v1/dashboard/analytics` | Required | Dimensions, companies, readiness |

### Mock Interview

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/mock` | Optional | Start timed session |
| PATCH | `/api/v1/mock/{id}` | — | Complete session with timing |

### AI Generator

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/generator` | — | Generate STAR answer from bullets |

### Coaching

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/coaching/invite` | Required | Invite student by email |
| GET | `/api/v1/coaching/students` | Required | Coach's student roster + stats |
| GET | `/api/v1/coaching/students/{id}/evaluations` | Required | Student's eval history |
| PATCH | `/api/v1/coaching/evaluations/{id}/coach-notes` | Required | Add/update feedback |
| GET | `/api/v1/coaching/invites` | Required | Pending invites for student |
| POST | `/api/v1/coaching/invites/{id}/accept` | Required | Accept invite |
| POST | `/api/v1/coaching/invites/{id}/decline` | Required | Decline invite |
| GET | `/api/v1/coaching/my-coaches` | Required | Student's active coaches |
| DELETE | `/api/v1/coaching/relationships/{id}` | Required | Remove relationship |

### Billing

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/billing/checkout` | Required | Create Stripe Checkout Session |
| GET | `/billing/status` | Required | Current tier + usage |
| POST | `/billing/webhook` | — | Stripe event handler |
| POST | `/billing/portal` | Required | Stripe Customer Portal session |

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Service info |
| GET | `/health` | Database + environment status |

---

## 8. Frontend Pages & Components

### Pages

| Route | Component | Auth | Description |
|-------|-----------|------|-------------|
| `/` | Dashboard | — | Stats + charts (auth) or feature cards (guest) |
| `/login` | LoginPage | — | Sign in / create account / OAuth |
| `/evaluate` | NewEvaluation | Protected | Company → role → question → answer → submit |
| `/evaluations/:id` | EvaluationDetail | Protected | Scores, feedback, revision, PDF download |
| `/mock` | MockInterview | Protected | Timed practice with countdown |
| `/generator` | AnswerGenerator | Protected | Bullet points → AI draft → review → evaluate |
| `/questions` | QuestionBank | — | Browse/filter/search 250+ questions |
| `/answers/:id/compare` | VersionComparison | Protected | Side-by-side version scores |
| `/analytics` | Analytics | Protected | Radar chart, readiness gauge, company breakdown |
| `/coaching` | CoachDashboard | Protected | Coach + student dual-mode view |
| `/moderation` | ModerationQueue | Protected | Moderator question review queue |
| `/pricing` | PricingPage | — | Free vs Pro tier comparison |
| `/billing/success` | PricingPage | Protected | Post-checkout confirmation |

### Shared Components

| Component | Purpose |
|-----------|---------|
| Layout | App shell: AppBar + sidebar + content area |
| ProtectedRoute | Auth guard with redirect to /login |
| UpgradePrompt | Tier limit dialog with upgrade CTA |
| ScoreBar | Visual 1–5 score bar with color coding |
| SimpleMarkdown | Lightweight markdown renderer for eval output |
| VoiceInput | Web Speech API microphone button |
| ErrorBoundary | React error boundary with friendly fallback |

---

## 9. AI Evaluation System

### Evaluation Framework

Claude evaluates answers across **6 dimensions**, each scored 1–5:

1. **Situation** — Context & Stakes: clarity, stakes, relevance
2. **Task** — Challenge & Responsibility: ownership, specificity, constraints
3. **Action** — Decision-Making & Judgment: reasoning, trade-offs, adaptability
4. **Result** — Measurable Impact & Reflection: quantified outcomes, learning
5. **Engagement** — Narrative Quality: clarity, pacing, specificity
6. **Overall** — Company Culture Alignment: values fit, role demonstration

### Evaluation Output Structure

1. Scored assessment (6 dimensions with justification)
2. STAR-by-STAR analysis (strengths + opportunities per section)
3. Rewrite suggestions and guiding questions
4. Company culture alignment analysis
5. Follow-up questions to expect (with why + how to prepare)
6. Alternative framing suggestions
7. Length & timing feedback
8. Interview readiness assessment with top 3 priorities

### Model Configuration

| Setting | Evaluation | Generator |
|---------|-----------|-----------|
| Model | claude-sonnet-4-20250514 | claude-sonnet-4-20250514 |
| Temperature | 0.3 (consistent) | 0.5 (creative) |
| Max tokens | 8,000 | 2,000 |

### Score Parsing

Regex-based extraction from Claude's markdown output:
- Pattern 1: `[4/5]` format
- Pattern 2: `Situation: 4/5` format
- Pattern 3: `**Situation**: 4/5` format

Also extracts: sections, follow-up questions, company alignment, average score.

### Interview Readiness Score

Weighted composite (0–100):
- **Score Quality** (40%): average score normalized to 0–100
- **Consistency** (30%): low variance across evaluations = higher score
- **Improvement Trend** (30%): positive slope over time = higher score

Labels: "Not Ready" | "Getting There" | "Interview Ready" | "Strong Candidate"

---

## 10. Authentication & Authorization

### JWT Tokens

| Token | Expiry | Purpose |
|-------|--------|---------|
| Access | 15 min | API authorization |
| Refresh | 7 days | Get new access token |

### OAuth Providers

- **Google**: Authorization Code flow, auto-link by email
- **GitHub**: Authorization Code flow, auto-link by email
- Tokens returned via URL fragment (#) for security

### Authorization Levels

| Level | Access |
|-------|--------|
| Anonymous | Companies, questions (read), answers (create) |
| Authenticated | Everything above + evaluations, dashboard, analytics, coaching |
| Moderator | Everything above + moderation queue |

### Axios Interceptor (Frontend)

- Attaches Bearer token to all requests
- On 401: queues requests, refreshes token, retries
- On refresh failure: clears tokens, redirects to /login

---

## 11. Monetization

### Tiers

| Feature | Free | Pro ($12/mo) |
|---------|------|-------------|
| Evaluations/month | 5 | Unlimited |
| STAR scoring | ✅ | ✅ |
| Company coaching | ✅ | ✅ |
| Question bank | ✅ | ✅ |
| AI generator | ✅ | ✅ |
| Analytics | ✅ | ✅ |
| PDF reports | ✅ | ✅ |
| Mock interviews | ✅ | ✅ |

### Stripe Integration

- **Checkout Sessions**: Hosted payment page (zero PCI burden)
- **Customer Portal**: Self-service subscription management
- **Webhooks**: `checkout.session.completed` → upgrade to Pro
- **Enforcement**: Per-user monthly counter checked before evaluation creation

---

## 12. Configuration & Deployment

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql+asyncpg://user:password@localhost/biae_db
ANTHROPIC_API_KEY=sk-ant-xxx
SECRET_KEY=your-secret-key-min-32-chars

# OAuth (optional — disables if empty)
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
GITHUB_CLIENT_ID=xxx
GITHUB_CLIENT_SECRET=xxx
OAUTH_REDIRECT_BASE=http://localhost:8000

# Stripe (optional — disables billing if empty)
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRO_PRICE_ID=price_xxx

# Application
APP_ENV=development
DEBUG=true
CORS_ORIGINS=http://localhost:3000
FRONTEND_URL=http://localhost:3000
FREE_EVALUATIONS_PER_MONTH=5
PRO_EVALUATIONS_PER_MONTH=999

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

### Running Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # edit with your values
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm start  # runs on port 3000
```

### Test Suite

| Suite | Count | Scope |
|-------|-------|-------|
| Backend (pytest) | 74 tests | Auth, answers, evaluations, questions, generator, mock, companies, score parsing, PDF, health |
| Frontend | — | Phase 3 planned |

### Directory Structure

```
biae/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + lifespan
│   │   ├── config.py            # Settings (env vars)
│   │   ├── database.py          # Async engine + sessions
│   │   ├── dependencies.py      # Auth + DB dependencies
│   │   ├── models/
│   │   │   └── models.py        # 8 SQLAlchemy models
│   │   ├── schemas/             # 7 Pydantic schema modules
│   │   ├── routers/             # 11 FastAPI routers
│   │   └── services/            # 8 service modules
│   ├── prompts/
│   │   └── STAR-eval-prompt_v1.md
│   ├── scripts/                 # SQL migrations
│   ├── tests/                   # 10 test suites (74 tests)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.ts        # Axios + types + 40+ API functions
│   │   ├── hooks/useAuth.tsx     # Auth context + provider
│   │   ├── components/          # 7 shared components
│   │   ├── pages/               # 12 page components
│   │   └── App.tsx              # Router + route definitions
│   ├── package.json
│   └── tsconfig.json
└── PRD.md                       # This document
```

---

## Commit History

| Hash | Description |
|------|-------------|
| `8dcb134` | feat: BIAE application — Milestones 1-10 |
| `b7a1b05` | feat: add auth UI, revision workflow, and version comparison |
| `24de374` | feat: enhance dashboard with stats, score trends, and recent evaluations |
| `d995323` | feat: add advanced analytics with radar chart, readiness score, and company breakdowns |
| `7a422af` | feat: add Google and GitHub OAuth authentication |
| `30fc1e1` | feat: add Stripe monetization with free/pro tiers and upgrade flow |
| `c2390be` | feat: add community question submissions with moderation queue |
| `cae8a98` | feat: add coaching relationships with invite workflow and feedback |
| `efe2ecc` | feat: add voice input for answer dictation via Web Speech API |
| `870ba25` | feat: mobile optimization pass across all pages |
