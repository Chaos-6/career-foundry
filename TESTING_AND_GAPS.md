# Career Foundry — Functional Test Plan & Gap Analysis

> **Purpose**: Complete functional test coverage from login through every user flow, plus data gap inventory for the next redesign phase.
> **Generated**: February 2026
> **Backend**: FastAPI + PostgreSQL | **Frontend**: React 19 + MUI v6

---

## Table of Contents

1. [Authentication Tests](#1-authentication-tests)
2. [Dashboard Tests](#2-dashboard-tests)
3. [New Evaluation — Standard Track](#3-new-evaluation--standard-track)
4. [New Evaluation — Agentic Track](#4-new-evaluation--agentic-track)
5. [Evaluation Detail & Post-Evaluation Actions](#5-evaluation-detail--post-evaluation-actions)
6. [Version Comparison](#6-version-comparison)
7. [Mock Interview](#7-mock-interview)
8. [AI Answer Generator](#8-ai-answer-generator)
9. [Question Bank](#9-question-bank)
10. [Answer Templates](#10-answer-templates)
11. [Coaching](#11-coaching)
12. [Moderation Queue](#12-moderation-queue)
13. [Billing & Tier Enforcement](#13-billing--tier-enforcement)
14. [Shared Evaluations](#14-shared-evaluations)
15. [Data Gap Analysis — Agentic Scenarios](#15-data-gap-analysis--agentic-scenarios)
16. [Data Gap Analysis — Question Bank](#16-data-gap-analysis--question-bank)
17. [Data Gap Analysis — Company Profiles](#17-data-gap-analysis--company-profiles)
18. [UX & Design Improvement Recommendations](#18-ux--design-improvement-recommendations)
19. [Dependency & Infrastructure Issues](#19-dependency--infrastructure-issues)

---

## 1. Authentication Tests

### 1.1 Registration (Create Account tab)
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 1.1.1 | Register with valid email + password (8+ chars) | Account created, tokens returned, redirected to dashboard |
| 1.1.2 | Register with password < 8 characters | Client-side error: "Password must be at least 8 characters" |
| 1.1.3 | Register with mismatched confirm password | Client-side error: "Passwords do not match" |
| 1.1.4 | Register with empty email or password | Client-side error: "Email and password are required" |
| 1.1.5 | Register with already-registered email | 409 error: "Email already registered" |
| 1.1.6 | Register with display name | Account created with display_name populated |
| 1.1.7 | Register without display name | Account created, display_name is null |
| 1.1.8 | Register > 5 times in 1 minute (same IP) | Rate limit: 429 error |

### 1.2 Login (Sign In tab)
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 1.2.1 | Login with valid credentials | Tokens returned, redirected to dashboard (or previous page) |
| 1.2.2 | Login with wrong password | 401: "Invalid email or password" |
| 1.2.3 | Login with non-existent email | 401: "Invalid email or password" (same message — no user enumeration) |
| 1.2.4 | Login with deactivated account | 403: "Account is deactivated" |
| 1.2.5 | Login with empty fields | Client-side error: "Email and password are required" |
| 1.2.6 | Login > 10 times in 1 minute (same IP) | Rate limit: 429 error |
| 1.2.7 | Login, then refresh page | Session persists via localStorage tokens |
| 1.2.8 | Login with redirect state (e.g., deep link to /evaluate) | After login, redirected to /evaluate (not dashboard) |

### 1.3 OAuth
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 1.3.1 | Click "Continue with Google" | Redirected to Google OAuth consent screen |
| 1.3.2 | Click "Continue with GitHub" | Redirected to GitHub OAuth authorization |
| 1.3.3 | Complete Google OAuth flow | Tokens in URL fragment, stored, redirected to dashboard |
| 1.3.4 | Complete GitHub OAuth flow | Same as Google |
| 1.3.5 | OAuth with unregistered email | New account auto-created |
| 1.3.6 | OAuth with previously registered email | Linked to existing account |
| 1.3.7 | OAuth with missing env config (no client ID) | Graceful error, not a crash |

### 1.4 Session Management
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 1.4.1 | Access token expires | Auto-refresh via interceptor, no user-visible interruption |
| 1.4.2 | Refresh token expires | Redirected to /login |
| 1.4.3 | Click Logout | Tokens cleared, redirected to login, sidebar updates |
| 1.4.4 | "Continue without signing in" link | Navigate to dashboard as unauthenticated user |

---

## 2. Dashboard Tests

### 2.1 Unauthenticated View
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 2.1.1 | Visit / without login | Hero banner with "Start Free Evaluation" and "Browse Questions" CTAs |
| 2.1.2 | Click "Start Free Evaluation" | Navigate to /evaluate (redirected to /login if protected) |
| 2.1.3 | Click "Browse Questions" | Navigate to /questions |
| 2.1.4 | Click feature cards (STAR, Mock, Generator, Question Bank) | Navigate to respective pages |
| 2.1.5 | Verify "How It Works" section renders | 5 steps visible |
| 2.1.6 | Verify credibility markers | "22+ companies", "80+ questions", "6 dimensions", "Claude AI" |

### 2.2 Authenticated View (No Evaluations)
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 2.2.1 | Fresh user with 0 evaluations | Stats show all zeros, empty recent table, no chart |
| 2.2.2 | Streak widget shows 0 days | No fire icon, "0 day streak" |
| 2.2.3 | Badges all locked | Badge icons greyed out with lock overlay |
| 2.2.4 | "Recommended for You" empty | No recommendations section (or empty state message) |

### 2.3 Authenticated View (With Evaluations)
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 2.3.1 | Stats summary cards | Total, average, best scores, monthly count correct |
| 2.3.2 | Score trend chart | Area chart with 30-day data, correct axes |
| 2.3.3 | Recent evaluations table | Shows last 10, clickable rows navigate to /evaluations/:id |
| 2.3.4 | Streak tracking | Current and longest streak, fire icon when active |
| 2.3.5 | Badge unlocking | Correct badges unlock at thresholds (verify each badge condition) |
| 2.3.6 | Recommended questions | Shows weak answers (score <= 3.5), sorted by days since practice |
| 2.3.7 | Click "Practice Again" on recommendation | Navigate to /evaluate with question pre-filled |

---

## 3. New Evaluation — Standard Track

### 3.1 Track Selection
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 3.1.1 | Default state | No track selected, Step 2 fields hidden |
| 3.1.2 | Select "Standard (STAR)" card | Standard fields appear (company, role, level) |
| 3.1.3 | Select "Agentic AI Engineer" card | Agentic fields appear (type, category) |
| 3.1.4 | Switch between tracks | Fields reset, previous selections cleared |

### 3.2 Standard Form Fields
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 3.2.1 | Company dropdown | Shows all 22 companies with principle_type |
| 3.2.2 | Role dropdown | 4 options: MLE, PM, TPM, EM |
| 3.2.3 | Experience level dropdown | 5 options: Entry, Mid, Senior, Staff+, Manager |
| 3.2.4 | All fields required | Submit disabled until company + role + level + question + answer filled |

### 3.3 Question Selection (Standard Track)

#### 3.3.1 "From Question Bank" tab
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 3.3.1a | Dropdown populated | Questions shown with text, competency tags, difficulty badge |
| 3.3.1b | "Surprise Me" button | Random question selected and displayed in alert |
| 3.3.1c | Select a question | Alert shows full question text |

#### 3.3.2 "Custom Question" tab
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 3.3.2a | Type custom question | Text field accepts input, submit enabled |
| 3.3.2b | Switch between tabs | Previous selection cleared |

### 3.4 Answer Input
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 3.4.1 | Type answer | Word counter updates in real-time |
| 3.4.2 | Answer < 50 words | Warning shown about length |
| 3.4.3 | Answer 200-400 words | Ideal range, no warning |
| 3.4.4 | Load from template | Template text populates textarea |
| 3.4.5 | Voice input (VoiceInput component) | Speech-to-text appends to textarea |

### 3.5 Bulk Import
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 3.5.1 | Drag-and-drop .txt file (< 100KB) | File parsed, answers listed |
| 3.5.2 | Drag-and-drop .md file (< 100KB) | File parsed, answers listed |
| 3.5.3 | File > 100KB | Error: file too large |
| 3.5.4 | Non .txt/.md file | Error: unsupported format |
| 3.5.5 | File with no parseable answers | Warning: 0 answers found |

### 3.6 Submit Standard Evaluation
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 3.6.1 | Submit with all fields valid | Answer + version created, evaluation queued, navigate to /evaluations/:id |
| 3.6.2 | Submit with empty answer | Validation error |
| 3.6.3 | Free user at limit (5 evals/month) | UpgradePrompt modal shown |
| 3.6.4 | Network error during submit | Error alert shown, form not cleared |

### 3.7 Standard Track — Every Company x Role Combination
| # | Company | MLE | PM | TPM | EM | Notes |
|---|---------|-----|-----|-----|-----|-------|
| 3.7.1-3.7.88 | Each of 22 companies | Test | Test | Test | Test | Verify question dropdown populates for each combo |

> **Note**: This is 88 combinations (22 companies x 4 roles). Many will share the same question pool since questions aren't company-specific in the bank. The key test is whether the evaluation completes successfully with each company's principles.

---

## 4. New Evaluation — Agentic Track

### 4.1 Agentic Form Fields
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 4.1.1 | Interview Type: Behavioral | Category dropdown shows 5 behavioral categories |
| 4.1.2 | Interview Type: System Design | Category dropdown shows only "architecture" |
| 4.1.3 | Category optional | Can submit without category (gets any scenario) |

### 4.2 Agentic Scenario Selection

#### 4.2.1 Behavioral + Each Category
| # | Type | Category | Scenarios Available | Status |
|---|------|----------|---------------------|--------|
| 4.2.1a | Behavioral | architecture_orchestration | 5 | OK |
| 4.2.1b | Behavioral | safety_alignment | 5 | OK |
| 4.2.1c | Behavioral | production_operations | 5 | OK |
| 4.2.1d | Behavioral | evaluation_metrics | 5 | OK |
| 4.2.1e | Behavioral | ethics_policy | 5 | OK |

#### 4.2.2 System Design + Each Category
| # | Type | Category | Scenarios Available | Status |
|---|------|----------|---------------------|--------|
| 4.2.2a | System Design | architecture | 5 | OK |
| 4.2.2b | System Design | architecture_orchestration | **0** | **GAP** |
| 4.2.2c | System Design | safety_alignment | **0** | **GAP** |
| 4.2.2d | System Design | production_operations | **0** | **GAP** |
| 4.2.2e | System Design | evaluation_metrics | **0** | **GAP** |
| 4.2.2f | System Design | ethics_policy | **0** | **GAP** |

> **GAP**: The category dropdown shows ALL categories regardless of interview type. When a user selects System Design + any category other than "architecture", the scenario dropdown is empty. Either filter categories by type, or add system design scenarios for each category.

#### 4.2.3 Custom Agentic Question
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 4.2.3a | Type custom agentic question | Scenario selection cleared, custom text used |
| 4.2.3b | Select scenario then type custom | Scenario deselected |
| 4.2.3c | Submit with custom question (no scenario) | Evaluation created with custom_question_text |

### 4.3 Submit Agentic Evaluation
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 4.3.1 | Submit behavioral agentic eval | Evaluation uses agentic behavioral prompt, 0-100 scoring |
| 4.3.2 | Submit system design agentic eval | Evaluation uses system design prompt, 0-100 scoring |
| 4.3.3 | Agentic eval without company | Works — target_company_id is nullable for agentic |
| 4.3.4 | Agentic eval result structure | Has agentic_scores, hiring_decision, the_diff section |

---

## 5. Evaluation Detail & Post-Evaluation Actions

### 5.1 Polling & Status Transitions
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 5.1.1 | Navigate to queued evaluation | Spinner + "queued" chip, polls every 2s |
| 5.1.2 | Status transitions to "analyzing" | Spinner + "analyzing" chip |
| 5.1.3 | Status transitions to "completed" | Full evaluation renders, polling stops |
| 5.1.4 | Status transitions to "failed" | Red error alert + "Try Again" button |

### 5.2 Standard Evaluation Results
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 5.2.1 | Score panel | 6 score bars (S/T/A/R/Engagement/Overall) + average |
| 5.2.2 | Score color coding | Green >= 4, Yellow >= 3, Red < 3 |
| 5.2.3 | Company alignment section | Shows aligned + reinforce principles |
| 5.2.4 | Full evaluation markdown | Renders correctly with headers, bullets, bold |
| 5.2.5 | Follow-up questions | Numbered list with question + why + how to prepare |

### 5.3 Agentic Evaluation Results
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 5.3.1 | Agentic score panel | 4 dimensions scored 0-100 |
| 5.3.2 | Hiring decision displayed | STRONG_HIRE / HIRE / BORDERLINE / REJECT |
| 5.3.3 | "The Diff" section | User critique vs Staff Engineer rewrite |
| 5.3.4 | Red flags + missing components | Lists displayed if present |

### 5.4 AI Improvement Suggestions
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 5.4.1 | Eval with all scores >= 4 | "Get AI Tips" button hidden (no weak dimensions) |
| 5.4.2 | Eval with scores <= 3 | "Get AI Tips" button visible |
| 5.4.3 | Click "Get AI Tips" | Loads suggestions per weak dimension |
| 5.4.4 | Suggestion cards | Show section chip + suggestion text + example |

### 5.5 Revision Flow
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 5.5.1 | Click "Revise & Re-Evaluate" | Revision editor expands with original answer pre-filled |
| 5.5.2 | Edit answer text | Word counter updates |
| 5.5.3 | Submit revision | New version created, new evaluation queued, navigate to new eval |
| 5.5.4 | Cancel revision | Editor collapses, no changes |
| 5.5.5 | Version chip shows correct number | "v2", "v3", etc. |

### 5.6 Other Actions
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 5.6.1 | Click "Compare Versions" | Navigate to /answers/:id/compare |
| 5.6.2 | Click "Download PDF" | PDF downloads with evaluation content |
| 5.6.3 | Click "Share" | Share token generated, URL copied to clipboard |
| 5.6.4 | Click "Revoke Share" | Share revoked, link no longer works |
| 5.6.5 | Click "Save as Template" | Template created from answer text |

---

## 6. Version Comparison

| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 6.1 | Navigate with 1 version | Single version card, no improvement summary |
| 6.2 | Navigate with 2+ versions | Improvement summary: "v1 → v3: +X.X points" |
| 6.3 | Score comparison table | All dimensions across versions, delta chips |
| 6.4 | Best score highlighted (bold) | Highest score per dimension in bold |
| 6.5 | Delta chips color coded | Green for improvement, red for decline, neutral |
| 6.6 | Version cards | Show word count, date, AI-assisted badge, avg score |
| 6.7 | "View Full Evaluation" per version | Navigate to correct /evaluations/:id |
| 6.8 | Latest version highlighted | 2px border + "Latest" chip |

---

## 7. Mock Interview

### 7.1 Setup Phase
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 7.1.1 | All dropdowns render | Company, Role, Level, Time Limit |
| 7.1.2 | Time limit options | 2 min, 3 min (recommended), 5 min, 10 min |
| 7.1.3 | Start button disabled until all fields selected | Cannot start without company + role + level |
| 7.1.4 | Click "Start Mock Interview" | Transitions to active phase |

### 7.2 Active Phase
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 7.2.1 | Timer counts down | MM:SS format, updates every second |
| 7.2.2 | Timer color at > 60s | Default color |
| 7.2.3 | Timer color at <= 60s | Orange warning |
| 7.2.4 | Timer color at <= 30s | Red urgent |
| 7.2.5 | Progress bar | Linear progress matches time remaining |
| 7.2.6 | Question displayed | Random question shown for selected filters |
| 7.2.7 | Type answer | Word counter updates, submit enabled at >= 10 words |
| 7.2.8 | Submit before timer ends | Answer + evaluation created, navigate to results |
| 7.2.9 | Timer reaches 0 with text | Auto-submit triggered |
| 7.2.10 | Timer reaches 0 without text | No submit (verify behavior) |
| 7.2.11 | Free user at limit | UpgradePrompt modal |

---

## 8. AI Answer Generator

### 8.1 Input Phase
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 8.1.1 | Context fields | Company, Role, Level dropdowns |
| 8.1.2 | Question selector | Dropdown from bank OR custom text field |
| 8.1.3 | STAR bullet inputs | 4 text areas: Situation, Task, Action, Result |
| 8.1.4 | Each bullet has placeholder | Context-appropriate placeholder text |
| 8.1.5 | Generate button disabled | Until company + role + level + question + at least some bullets |
| 8.1.6 | Click "Generate STAR Answer" | Loading spinner, then transitions to editing phase |
| 8.1.7 | Rate limit (> 5/min) | 429 error shown |

### 8.2 Editing Phase
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 8.2.1 | AI output displayed | Pre-filled textarea with generated narrative |
| 8.2.2 | Generation metadata | Chip showing "AI generated in X.Xs" |
| 8.2.3 | Edit the generated text | Word counter updates |
| 8.2.4 | Click "Reset to Original" | Textarea reverts to AI output |
| 8.2.5 | Click "Start Over" | Returns to input phase, all fields reset |
| 8.2.6 | Click "Submit for Evaluation" | Answer + evaluation created, navigate to results |

---

## 9. Question Bank

### 9.1 Browsing & Filtering
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 9.1.1 | Page loads | Shows all approved questions with total count |
| 9.1.2 | Filter by Role: MLE | Only MLE-tagged questions |
| 9.1.3 | Filter by Role: PM | Only PM-tagged questions |
| 9.1.4 | Filter by Role: TPM | Only TPM-tagged questions |
| 9.1.5 | Filter by Role: EM | Only EM-tagged questions |
| 9.1.6 | Filter by Difficulty: standard | Only standard difficulty |
| 9.1.7 | Filter by Difficulty: advanced | Only advanced difficulty |
| 9.1.8 | Filter by Difficulty: senior_plus | Only senior_plus difficulty |
| 9.1.9 | Filter by Level: entry through manager | Each level shows matching questions |
| 9.1.10 | Filter by each of 13 competencies | Results returned for each (see data gaps below) |
| 9.1.11 | Search by keyword | Text search matches question_text |
| 9.1.12 | Combine multiple filters | Intersection of all active filters |
| 9.1.13 | Clear all filters | Returns to full question list |
| 9.1.14 | Empty results | "No questions found" + "Clear All Filters" button |
| 9.1.15 | Click competency chip on question | Filters by that competency |
| 9.1.16 | Click role chip on question | Filters by that role |

### 9.2 Question Actions
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 9.2.1 | Click "Practice" on question | Navigate to /evaluate with question pre-filled |
| 9.2.2 | Click "Mock" on question | Navigate to /mock with question pre-filled |
| 9.2.3 | Click "AI Draft" on question | Navigate to /generator with question pre-filled |
| 9.2.4 | Click "Random Question" | Random question fetched, navigates to /evaluate |

### 9.3 Community Submission (Authenticated)
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 9.3.1 | Click "Submit Question" | Dialog opens |
| 9.3.2 | Submit with valid question (20+ chars) | Success alert, question added to pending queue |
| 9.3.3 | Submit with < 20 characters | Validation error |
| 9.3.4 | Submit with > 500 characters | Character limit enforced |
| 9.3.5 | Add role tags, competency tags, difficulty, level | All saved with submission |
| 9.3.6 | Submit duplicate question | Error or warning |
| 9.3.7 | "Submit Question" hidden when unauthenticated | Button not rendered |

---

## 10. Answer Templates

| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 10.1 | No templates exist | Empty state with "Create Your First Template" CTA |
| 10.2 | Click "New Template" | Editor expands with empty fields |
| 10.3 | Fill name + template text | Required fields populated |
| 10.4 | Toggle role tag chips | Selected tags highlighted |
| 10.5 | Toggle competency tag chips | Selected tags highlighted |
| 10.6 | Save template | Template appears in list |
| 10.7 | Click edit on template | Editor populates with template data |
| 10.8 | Update template | Changes saved, list refreshes |
| 10.9 | Delete template | Confirmation dialog → template removed |
| 10.10 | Set template as default | Pin icon filled, previous default unpinned |
| 10.11 | Only one default at a time | Setting new default clears old one |
| 10.12 | Template usage count | Increments when loaded in /evaluate |
| 10.13 | Template sort order | Defaults first, then by newest |

---

## 11. Coaching

### 11.1 Coach Actions
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 11.1.1 | Invite student by email | Success message, invite created as "pending" |
| 11.1.2 | Invite already-connected student | Error: duplicate relationship |
| 11.1.3 | Self-invite | Error: cannot invite yourself |
| 11.1.4 | Invite non-registered email | Invite created, auto-linked when they register |
| 11.1.5 | View student list | Active students with stats (evals, avg, best) |
| 11.1.6 | Click student card | Expands to show evaluation history |
| 11.1.7 | Add coach notes to evaluation | Notes saved with focus areas |
| 11.1.8 | Remove student | Relationship revoked |

### 11.2 Student Actions
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 11.2.1 | View pending invites | Shows invites with coach name/email |
| 11.2.2 | Accept invite | Relationship becomes "active" |
| 11.2.3 | Decline invite | Invite removed |
| 11.2.4 | View "My Coaches" | Lists active coaches |
| 11.2.5 | Remove coach | Relationship revoked |

### 11.3 No invites/students
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 11.3.1 | Coach with no students | Empty students section |
| 11.3.2 | Student with no invites | No "Pending Invites" section rendered |
| 11.3.3 | Student with no coaches | No "My Coaches" section rendered |

---

## 12. Moderation Queue

| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 12.1 | Non-moderator visits /moderation | Error or redirect (not accessible) |
| 12.2 | Moderator with pending questions | Question cards with Approve/Reject buttons |
| 12.3 | Click "Approve" | Question status → "approved", appears in public bank |
| 12.4 | Click "Reject" | Dialog opens, reason required |
| 12.5 | Submit rejection without reason | Validation error |
| 12.6 | Submit rejection with reason | Question status → "rejected", removed from queue |
| 12.7 | Empty queue | "No questions pending review" empty state |
| 12.8 | Card disappears after action | Optimistic UI update |

---

## 13. Billing & Tier Enforcement

### 13.1 Free Tier
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 13.1.1 | Free user submits eval 1-5 | Evaluations succeed normally |
| 13.1.2 | Free user submits eval 6 | 403 TIER_LIMIT_REACHED → UpgradePrompt modal |
| 13.1.3 | Free user on /pricing | Shows "Current Plan" chip on Free card |
| 13.1.4 | Free user clicks "Upgrade to Pro" | Stripe Checkout session created, redirect |
| 13.1.5 | Monthly eval counter | Shows "X of 5 free evaluations" |

### 13.2 Pro Tier
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 13.2.1 | Pro user submits unlimited evals | No tier limit hit (999/month) |
| 13.2.2 | Pro user on /pricing | Shows "Current Plan" chip on Pro card |
| 13.2.3 | Pro user clicks "Manage Subscription" | Stripe Customer Portal opens |
| 13.2.4 | Pro user downgrades via Stripe | Webhook sets tier back to "free" |

### 13.3 Stripe Integration
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 13.3.1 | Checkout success redirect | /billing/success shows success alert |
| 13.3.2 | Webhook: checkout.session.completed | User tier updated to "pro" |
| 13.3.3 | Webhook: customer.subscription.deleted | User tier reverted to "free" |
| 13.3.4 | Stripe config missing | 503 error (not a crash) |

---

## 14. Shared Evaluations

| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 14.1 | Visit /shared/:valid_token | Public read-only evaluation view |
| 14.2 | Visit /shared/:invalid_token | Error: "invalid or expired" |
| 14.3 | Visit /shared/:revoked_token | Error: "invalid or expired" |
| 14.4 | Shared view content | Scores, alignment, questions — NO answer text, NO user info |
| 14.5 | Share footer | "Generated by Career Foundry" branding |

---

## 15. Data Gap Analysis — Agentic Scenarios

### 15.1 Zero-Result Filter Combinations (Verified)

The category dropdown shows ALL 6 categories regardless of selected interview type. This creates **5 dead-end paths** where users see an empty scenario list:

| Interview Type | Category | Scenarios | Status |
|---------------|----------|-----------|--------|
| System Design | architecture_orchestration | **0** | **BROKEN** |
| System Design | safety_alignment | **0** | **BROKEN** |
| System Design | production_operations | **0** | **BROKEN** |
| System Design | evaluation_metrics | **0** | **BROKEN** |
| System Design | ethics_policy | **0** | **BROKEN** |
| System Design | architecture | 5 | OK |
| Behavioral | architecture_orchestration | 5 | OK |
| Behavioral | safety_alignment | 5 | OK |
| Behavioral | production_operations | 5 | OK |
| Behavioral | evaluation_metrics | 5 | OK |
| Behavioral | ethics_policy | 5 | OK |
| Behavioral | architecture | **0** | **BROKEN** |

### 15.2 Difficulty Distribution Gap

| Type | Hard | Expert | Total |
|------|------|--------|-------|
| Behavioral | 19 | 6 | 25 |
| System Design | **0** | 5 | 5 |

**Gap**: No "hard" difficulty system design scenarios. Users wanting to start with easier system design have nothing to practice with.

### 15.3 Recommendations for Agentic Scenarios

1. **Filter categories by interview type** — Don't show categories that have no scenarios for the selected type
2. **Add 10-15 system design scenarios** across all categories (not just "architecture")
3. **Add "hard" difficulty system design scenarios** — Currently all are "expert"
4. **Consider adding non-AGENTIC_ENGINEER roles** — PMs designing agent products, EMs managing agentic teams

---

## 16. Data Gap Analysis — Question Bank

### 16.1 Role + Level Matrix (Verified via API)

| Role | Entry | Mid | Senior | Staff | Manager |
|------|-------|-----|--------|-------|---------|
| MLE | 23 | 29 | 16 | **1** | **0** |
| PM | 30 | 32 | 11 | **2** | **0** |
| TPM | 14 | 27 | 14 | **3** | **0** |
| EM | **7** | **7** | **2** | **0** | 60 |

**Critical Gaps**:
- **Staff level**: Only 1-3 questions per role. Staff+ engineers have almost nothing to practice.
- **MLE Manager**: 0 questions. No ML engineering manager path.
- **PM Manager**: 0 questions. No PM manager path.
- **TPM Manager**: 0 questions. No TPM manager path.
- **EM Entry/Mid**: Only 7 questions each. Very thin for early-career EMs.
- **EM Senior**: Only 2 questions. Nearly empty.

### 16.2 Sparse Competency + Role Combinations (Verified)

| Role | Competency | Count | Status |
|------|-----------|-------|--------|
| MLE | mentorship | 3 | **SPARSE** |
| PM | mentorship | 2 | **SPARSE** |
| TPM | mentorship | 2 | **SPARSE** |
| EM | customer_obsession | 1 | **NEARLY EMPTY** |

### 16.3 Level Band Coverage

**68% of questions (336 of ~493) have NULL level_band.** This means:
- When a user filters by any level, they only see ~32% of questions
- The "All Levels" filter shows everything, creating a jarring difference in count
- Users filtering by "Senior" see only 18 questions across all roles

### 16.4 Recommendations for Question Bank

1. **Backfill level_band** on all 336 NULL questions — Assign based on difficulty heuristic:
   - `standard` → `entry` or `mid`
   - `advanced` → `mid` or `senior`
   - `senior_plus` → `senior` or `staff`
2. **Add 20-30 staff+ level questions** across all roles
3. **Add manager-level questions** for MLE, PM, TPM (not just EM)
4. **Expand EM entry/mid questions** from 7 to 20+ each
5. **Add mentorship questions** across all roles (currently only 18 total)
6. **Add customer_obsession questions** for EM role (currently 1)

---

## 17. Data Gap Analysis — Company Profiles

### 17.1 Current Coverage (22 companies)

**Well-covered**: Amazon (16 principles), Google, Meta, Microsoft, Apple
**Adequate**: Netflix, Uber, Airbnb, Stripe, Salesforce, NVIDIA, LinkedIn, Oracle
**Minimal**: OpenAI (5 principles), Anthropic (4), Databricks, Snowflake

### 17.2 Missing Companies (Commonly Asked For)
- **AI/ML**: Hugging Face, Cohere, Scale AI, Midjourney, Stability AI
- **Fintech**: PayPal, Revolut, Plaid, Affirm, Robinhood
- **Big Tech**: Samsung, Intel, Qualcomm, AMD
- **Cloud**: Cloudflare, Vercel, Netlify, Supabase
- **Enterprise**: Twilio, Atlassian, ServiceNow, Workday

### 17.3 Potential Duplicate

Netflix may appear twice in seed data with different `principle_type` values ("Core Values" and "Core Principles"). Verify and deduplicate.

---

## 18. UX & Design Improvement Recommendations

### 18.1 Empty State Handling
| Issue | Location | Recommendation |
|-------|----------|----------------|
| No empty state for zero-result agentic scenario filters | NewEvaluation (agentic) | Show "No scenarios match this combination. Try a different category." with suggestion |
| Question bank level filter misleading | QuestionBank | Show count per filter option, or grey out options with 0 results |
| Staff+ level shows 1-3 results | QuestionBank | Add banner: "Limited questions at this level — more coming soon" |

### 18.2 Navigation & Flow Gaps
| Issue | Recommendation |
|-------|----------------|
| No way to navigate from evaluation detail back to the question it answered | Add "View Question" link on evaluation detail |
| No breadcrumb trail on nested pages | Add breadcrumbs: Dashboard > Evaluation > Compare |
| Coaching page serves dual role (coach + student) | Consider splitting into /coaching/students and /coaching/my-coaches |

### 18.3 Missing Features to Consider
| Feature | Priority | Rationale |
|---------|----------|-----------|
| Export evaluation history as CSV | Medium | Users preparing for job search want bulk data |
| Dark mode toggle | Low | Common ask, MUI v6 supports it |
| Keyboard shortcuts for mock interview | Medium | Power users want keyboard-driven flow |
| "Compare to AI ideal" in agentic track | High | Staff Engineer rewrite exists but no side-by-side diff |
| Question bookmarks/favorites | Medium | Users want to save questions for later practice |
| Practice session scheduling/reminders | Low | Spaced repetition exists but is passive |

### 18.4 Accessibility Concerns
| Issue | Recommendation |
|-------|----------------|
| Score colors (red/green) only signal | Add text labels alongside colors |
| Timer in mock interview is visual only | Add audio alert at 60s, 30s, 10s |
| Voice input has no visual feedback during recording | Add pulsing indicator |

---

## 19. Dependency & Infrastructure Issues

### 19.1 Confirmed Issues (Fixed in This Session)

| Issue | Fix Applied | File |
|-------|------------|------|
| `email-validator` missing from requirements | Added `email-validator>=2.0.0,<3.0.0` | `backend/requirements.txt` |
| `passlib` incompatible with `bcrypt >= 4.1` | Added `bcrypt>=4.0.0,<4.1.0` pin | `backend/requirements.txt` |
| `.env` DATABASE_URL wrong for local Postgres | Updated to match PostgreSQL 16 install | `backend/.env` |

### 19.2 Remaining Concerns

| Issue | Risk | Recommendation |
|-------|------|----------------|
| `passlib` unmaintained since 2020 | High — future Python/bcrypt versions may break | Migrate to `bcrypt` directly or `argon2-cffi` |
| `python-jose` last release 2022 | Medium — JWT library stagnant | Consider `PyJWT` as replacement |
| Two PostgreSQL installs (Homebrew 15 + System 16) | Low — confusion risk | Remove unused Homebrew install |
| No Alembic migration for schema changes | High — production risk | Set up Alembic before next deploy |
| `SECRET_KEY=change-me-in-production` | Critical if deployed | Generate a real secret for production |
| `ANTHROPIC_API_KEY=sk-ant-...` placeholder | Critical | Must set real key for evaluations to work |
| Stripe webhook secret not configured | Medium | Billing features return 503 without it |

---

## Test Execution Priority

### Phase 1: Core Path (Do First)
- 1.1-1.2 (Auth), 3.1-3.6 (Standard Eval), 5.1-5.2 (Results)

### Phase 2: Feature Coverage
- 4.1-4.3 (Agentic Eval), 7.1-7.2 (Mock), 8.1-8.2 (Generator), 9.1-9.3 (Question Bank)

### Phase 3: Secondary Features
- 10 (Templates), 11 (Coaching), 12 (Moderation), 6 (Version Compare)

### Phase 4: Business Logic
- 13 (Billing), 14 (Sharing)

### Phase 5: Data Gap Resolution
- Sections 15-17 (Feed into redesign backlog)
