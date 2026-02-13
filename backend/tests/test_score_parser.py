"""Tests for the score parser module.

These are pure unit tests — no database, no API calls. They verify that
the regex patterns correctly extract scores from Claude's evaluation
markdown output, handling format variations.
"""

from decimal import Decimal

from app.services.score_parser import (
    parse_company_alignment,
    parse_follow_up_questions,
    parse_scores,
    parse_sections,
)


# ---------------------------------------------------------------------------
# Sample evaluation markdown (mimics Claude's actual output)
# ---------------------------------------------------------------------------

SAMPLE_EVALUATION = """
## DIMENSION SCORES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Situation – Context & Stakes           [4/5]
2. Task – Challenge & Responsibility      [3/5]
3. Action – Decision-Making & Judgment    [4/5]
4. Result – Measurable Impact             [5/5]
5. Engagement & Delivery                  [3/5]
6. Overall Interview Readiness            [4/5]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AVERAGE SCORE: [3.8/5]

### A. SCORED ASSESSMENT (Detailed Breakdown)

**1. Situation – Context & Stakes: 4/5**
**Why:** The candidate clearly establishes context with a specific ML pipeline failure...

**2. Task – Challenge & Responsibility: 3/5**
**Why:** While the responsibility is stated, it could be more specific...

### B. STAR-BY-STAR ANALYSIS

#### SITUATION
- **Strengths:** Clear opening with technical context
- **Opportunities:** Could quantify business impact earlier

#### TASK
- **Strengths:** Personal ownership is evident
- **Opportunities:** Add constraints and timeline

#### ACTION
- **Strengths:** Good technical depth on data analysis approach
- **Opportunities:** Missing trade-off discussion

#### RESULT
- **Strengths:** Excellent quantification (78% to 94%)
- **Opportunities:** Add broader organizational impact

### C. SPECIFIC REWRITE SUGGESTIONS & GUIDING QUESTIONS

**Approach Option 1:** Instead of "I was responsible for debugging..."
Try: "I personally led the investigation into..."

### D. COMPANY CULTURE ALIGNMENT & VALUES FIT

**Amazon Culture Map:**
- **Key LPs for this role:** "Dive Deep," "Earn Trust," "Deliver Results"
- **How Your Answer Aligns:** Your answer shows "Dive Deep" through the technical investigation and "Deliver Results" via quantified outcomes.
- **Where to Reinforce:** Consider emphasizing how you "Earned Trust" by communicating transparently throughout the process.

### E. FOLLOW-UP QUESTIONS TO EXPECT

**Likely Follow-Ups:**
1. "What specific data distribution shifts did you identify?"
   - *Why it might be asked:* To probe technical depth
   - *How to prepare:* Have 2-3 specific examples ready

2. "How did you communicate the timeline to stakeholders?"
   - *Why it might be asked:* To assess communication skills
   - *How to prepare:* Describe your update cadence

3. "What would you do differently next time?"
   - *Why it might be asked:* To test self-awareness

### F. ALTERNATIVE FRAMING SUGGESTIONS

**Framing Option 1 – Leadership Focus:**
"If you want to emphasize leadership, lead with the cross-team coordination..."

### G. LENGTH & TIMING FEEDBACK

**Current Estimated Timing:**
- Situation: 20 seconds — Good
- Task: 15 seconds — Good
- Action: 45 seconds — Slightly short
- Result: 15 seconds — Good
- **Total: 95 seconds** — On the shorter side

### H. INTERVIEW-READY ASSESSMENT & FINAL RECOMMENDATION

**Is this answer interview-ready?**
- [x] **Yes, with minor tweaks.** Address the 1-2 improvements below.

**Top 3 Priorities:**
1. Quantify the business impact in the Situation
2. Add trade-off discussion to Action
3. Expand Result to include organizational impact
"""


class TestParseScores:
    """Test score extraction from evaluation markdown."""

    def test_extracts_all_bracket_scores(self):
        """Bracket format [X/5] should be parsed correctly."""
        scores = parse_scores(SAMPLE_EVALUATION)
        assert scores.situation_score == 4
        assert scores.task_score == 3
        assert scores.action_score == 4
        assert scores.result_score == 5
        assert scores.engagement_score == 3
        assert scores.overall_score == 4

    def test_extracts_average(self):
        """AVERAGE SCORE line should be parsed."""
        scores = parse_scores(SAMPLE_EVALUATION)
        assert scores.average_score == Decimal("3.8")

    def test_all_scores_present(self):
        """all_scores_present should be True when all 6 scores found."""
        scores = parse_scores(SAMPLE_EVALUATION)
        assert scores.all_scores_present is True

    def test_calculates_average_when_missing(self):
        """If AVERAGE SCORE line is missing, calculate from individual scores."""
        # Remove the average line
        modified = SAMPLE_EVALUATION.replace("AVERAGE SCORE: [3.8/5]", "")
        scores = parse_scores(modified)
        assert scores.all_scores_present is True
        # (4+3+4+5+3+4)/6 = 3.8333... → 3.8
        assert scores.average_score == Decimal("3.8")

    def test_colon_format_scores(self):
        """Colon format 'Dimension: X/5' should also work."""
        colon_markdown = """
        Situation – Context & Stakes: 4/5
        Task – Challenge & Responsibility: 3/5
        Action – Decision-Making & Judgment: 5/5
        Result – Measurable Impact: 4/5
        Engagement & Delivery: 3/5
        Overall Interview Readiness: 4/5
        """
        scores = parse_scores(colon_markdown)
        assert scores.situation_score == 4
        assert scores.task_score == 3
        assert scores.action_score == 5
        assert scores.result_score == 4
        assert scores.engagement_score == 3
        assert scores.overall_score == 4

    def test_bold_format_scores(self):
        """Bold format '**Dimension**: X/5' should also work."""
        bold_markdown = """
        **Situation – Context & Stakes**: 4/5
        **Task – Challenge & Responsibility**: 3/5
        **Action – Decision-Making & Judgment**: 5/5
        **Result – Measurable Impact**: 4/5
        **Engagement & Delivery**: 3/5
        **Overall Interview Readiness**: 4/5
        """
        scores = parse_scores(bold_markdown)
        assert scores.situation_score == 4
        assert scores.action_score == 5

    def test_handles_no_scores(self):
        """Empty or unparseable markdown returns None scores."""
        scores = parse_scores("No scores here!")
        assert scores.situation_score is None
        assert scores.all_scores_present is False
        assert scores.average_score is None

    def test_rejects_out_of_range_scores(self):
        """Scores outside 1-5 should be rejected."""
        bad_markdown = """
        1. Situation – Context & Stakes           [0/5]
        2. Task – Challenge & Responsibility      [6/5]
        """
        scores = parse_scores(bad_markdown)
        assert scores.situation_score is None  # 0 is out of range
        assert scores.task_score is None  # 6 is out of range


class TestParseSections:
    """Test section extraction from evaluation markdown."""

    def test_extracts_sections(self):
        """Should extract section text keyed by section name."""
        sections = parse_sections(SAMPLE_EVALUATION)
        assert "scored_assessment" in sections
        assert "star_analysis" in sections
        assert "company_alignment" in sections
        assert "follow_up_questions" in sections
        assert "interview_ready" in sections

    def test_sections_contain_content(self):
        """Extracted sections should contain meaningful content."""
        sections = parse_sections(SAMPLE_EVALUATION)
        assert "Situation" in sections.get("scored_assessment", "")
        assert "STAR" in sections.get("star_analysis", "")

    def test_handles_empty_markdown(self):
        """Empty markdown returns empty dict."""
        sections = parse_sections("")
        assert sections == {}


class TestParseFollowUpQuestions:
    """Test follow-up question extraction."""

    def test_extracts_questions(self):
        """Should extract follow-up questions from section E."""
        questions = parse_follow_up_questions(SAMPLE_EVALUATION)
        assert len(questions) >= 1
        # First question should mention data distribution
        assert any("data" in q["question"].lower() for q in questions)

    def test_handles_no_section(self):
        """Returns empty list if no follow-up section found."""
        questions = parse_follow_up_questions("No follow-up section here.")
        assert questions == []


class TestParseCompanyAlignment:
    """Test company alignment extraction."""

    def test_extracts_alignment(self):
        """Should extract alignment details."""
        alignment = parse_company_alignment(SAMPLE_EVALUATION, "Amazon")
        assert alignment["company"] == "Amazon"

    def test_handles_no_section(self):
        """Returns default dict if no alignment section found."""
        alignment = parse_company_alignment("Nothing here.", "Amazon")
        assert alignment["company"] == "Amazon"
        assert alignment["aligned_principles"] == []
