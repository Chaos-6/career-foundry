"""
PDF report generation for STAR evaluations.

Generates a professional, printable PDF from a completed evaluation.
Uses ReportLab Platypus (flowable-based layout) for automatic pagination.

The report includes:
- Candidate context header
- 6-dimension score table with color-coded status
- STAR-by-STAR analysis
- Company alignment section
- Follow-up questions
- Top 3 priorities
- Interview readiness assessment

Design: Platypus flowables (not raw Canvas) for simplicity and auto-pagination.
On-demand generation — no pre-storage needed.
"""

import re
from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Brand Colors
# ---------------------------------------------------------------------------

BRAND_PRIMARY = colors.HexColor("#1a365d")      # Navy — headings
BRAND_SECONDARY = colors.HexColor("#2b6cb0")    # Blue — subheadings
BRAND_ACCENT = colors.HexColor("#38a169")        # Green — good scores
BRAND_CAUTION = colors.HexColor("#d69e2e")       # Amber — average scores
BRAND_DANGER = colors.HexColor("#e53e3e")        # Red — low scores
BRAND_TEXT = colors.HexColor("#2d3748")          # Dark gray — body text
BRAND_MUTED = colors.HexColor("#718096")         # Muted gray — labels
BRAND_LIGHT_BG = colors.HexColor("#f7fafc")      # Light gray — table backgrounds
BRAND_BORDER = colors.HexColor("#e2e8f0")        # Border gray


def _score_color(score: int | None) -> colors.Color:
    """Get a color for a score value (1-5)."""
    if score is None:
        return BRAND_MUTED
    if score >= 4:
        return BRAND_ACCENT
    if score >= 3:
        return BRAND_CAUTION
    return BRAND_DANGER


def _score_label(score: int | None) -> str:
    """Get a human-readable label for a score."""
    if score is None:
        return "N/A"
    labels = {5: "Exceptional", 4: "Strong", 3: "Solid", 2: "Needs Work", 1: "Off-Track"}
    return labels.get(score, str(score))


# ---------------------------------------------------------------------------
# Style Builder
# ---------------------------------------------------------------------------

def _build_styles() -> dict:
    """Build the full set of paragraph styles for the report."""
    base = getSampleStyleSheet()
    styles = {}

    styles["title"] = ParagraphStyle(
        "ReportTitle",
        parent=base["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=BRAND_PRIMARY,
        spaceAfter=6,
        alignment=TA_LEFT,
    )
    styles["subtitle"] = ParagraphStyle(
        "ReportSubtitle",
        fontName="Helvetica",
        fontSize=11,
        textColor=BRAND_MUTED,
        spaceAfter=12,
    )
    styles["h2"] = ParagraphStyle(
        "SectionHeading",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=15,
        textColor=BRAND_PRIMARY,
        spaceBefore=18,
        spaceAfter=8,
    )
    styles["h3"] = ParagraphStyle(
        "SubsectionHeading",
        parent=base["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=BRAND_SECONDARY,
        spaceBefore=10,
        spaceAfter=4,
    )
    styles["body"] = ParagraphStyle(
        "BodyText",
        fontName="Helvetica",
        fontSize=10,
        textColor=BRAND_TEXT,
        leading=14,
        spaceAfter=6,
    )
    styles["bullet"] = ParagraphStyle(
        "BulletText",
        fontName="Helvetica",
        fontSize=10,
        textColor=BRAND_TEXT,
        leading=14,
        leftIndent=20,
        spaceAfter=4,
        bulletIndent=8,
    )
    styles["score_label"] = ParagraphStyle(
        "ScoreLabel",
        fontName="Helvetica",
        fontSize=10,
        textColor=BRAND_TEXT,
    )
    styles["score_value"] = ParagraphStyle(
        "ScoreValue",
        fontName="Helvetica-Bold",
        fontSize=10,
        alignment=TA_CENTER,
    )
    styles["footer"] = ParagraphStyle(
        "FooterText",
        fontName="Helvetica",
        fontSize=8,
        textColor=BRAND_MUTED,
        alignment=TA_CENTER,
    )
    styles["strength_label"] = ParagraphStyle(
        "StrengthLabel",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=BRAND_ACCENT,
        spaceAfter=2,
    )
    styles["opportunity_label"] = ParagraphStyle(
        "OpportunityLabel",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=BRAND_CAUTION,
        spaceAfter=2,
    )

    return styles


# ---------------------------------------------------------------------------
# Safe text helper
# ---------------------------------------------------------------------------

def _safe(text: str) -> str:
    """XML-escape text for ReportLab's markup parser, preserving bold/italic."""
    if not text:
        return ""
    # Escape ampersands and angle brackets
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    # Restore intentional markup
    for tag in ["b", "i", "u"]:
        text = text.replace(f"&lt;{tag}&gt;", f"<{tag}>")
        text = text.replace(f"&lt;/{tag}&gt;", f"</{tag}>")
    return text


# ---------------------------------------------------------------------------
# PDF Report Generator
# ---------------------------------------------------------------------------

class PDFReportGenerator:
    """Generates professional PDF reports from completed evaluations."""

    def __init__(self):
        self.styles = _build_styles()

    def generate_evaluation_report(
        self,
        *,
        company_name: str,
        target_role: str,
        experience_level: str,
        question_text: str,
        answer_text: str,
        word_count: int | None,
        situation_score: int | None,
        task_score: int | None,
        action_score: int | None,
        result_score: int | None,
        engagement_score: int | None,
        overall_score: int | None,
        average_score: Decimal | None,
        evaluation_markdown: str | None,
        company_alignment: dict | None,
        follow_up_questions: list[dict] | None,
        evaluation_sections: dict | None,
    ) -> bytes:
        """Generate the full evaluation PDF report.

        Returns raw PDF bytes suitable for streaming as a Response.
        """
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            title=f"STAR Evaluation - {company_name} {target_role}",
            author="Behavioral Interview Answer Evaluator",
        )

        story = []

        # --- Title & Context ---
        self._render_header(
            story,
            company_name=company_name,
            target_role=target_role,
            experience_level=experience_level,
        )

        # --- Question ---
        story.append(Paragraph("Interview Question", self.styles["h2"]))
        story.append(Paragraph(_safe(question_text), self.styles["body"]))
        story.append(Spacer(1, 8))

        # --- Score Table ---
        self._render_score_table(
            story,
            situation_score=situation_score,
            task_score=task_score,
            action_score=action_score,
            result_score=result_score,
            engagement_score=engagement_score,
            overall_score=overall_score,
            average_score=average_score,
        )

        # --- STAR-by-STAR Analysis ---
        if evaluation_sections:
            self._render_star_analysis(story, evaluation_sections)

        # --- Company Alignment ---
        if company_alignment:
            self._render_company_alignment(story, company_alignment, company_name)

        # --- Follow-up Questions ---
        if follow_up_questions:
            self._render_follow_up_questions(story, follow_up_questions)

        # --- Interview Readiness & Top Priorities ---
        if evaluation_sections and "interview_ready" in evaluation_sections:
            self._render_interview_readiness(story, evaluation_sections["interview_ready"])

        # --- Footer ---
        story.append(Spacer(1, 20))
        story.append(
            HRFlowable(
                width="100%",
                thickness=0.5,
                color=BRAND_BORDER,
                spaceAfter=8,
            )
        )
        now = datetime.now(timezone.utc).strftime("%B %d, %Y")
        story.append(
            Paragraph(
                f"Generated by Behavioral Interview Answer Evaluator &bull; {now}",
                self.styles["footer"],
            )
        )

        doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
        return buffer.getvalue()

    # -----------------------------------------------------------------------
    # Section renderers
    # -----------------------------------------------------------------------

    def _render_header(
        self,
        story: list,
        *,
        company_name: str,
        target_role: str,
        experience_level: str,
    ):
        """Render the report title and candidate context."""
        story.append(Paragraph("STAR Evaluation Report", self.styles["title"]))
        story.append(
            Paragraph(
                f"{company_name} &bull; {target_role} &bull; {experience_level.title()}",
                self.styles["subtitle"],
            )
        )
        story.append(
            HRFlowable(
                width="100%",
                thickness=1.5,
                color=BRAND_PRIMARY,
                spaceAfter=12,
            )
        )

    def _render_score_table(
        self,
        story: list,
        *,
        situation_score: int | None,
        task_score: int | None,
        action_score: int | None,
        result_score: int | None,
        engagement_score: int | None,
        overall_score: int | None,
        average_score: Decimal | None,
    ):
        """Render the 6-dimension score table with color coding."""
        story.append(Paragraph("Dimension Scores", self.styles["h2"]))

        dimensions = [
            ("Situation — Context & Stakes", situation_score),
            ("Task — Challenge & Responsibility", task_score),
            ("Action — Decision-Making & Judgment", action_score),
            ("Result — Measurable Impact", result_score),
            ("Engagement & Delivery", engagement_score),
            ("Overall Interview Readiness", overall_score),
        ]

        # Header row
        header = [
            Paragraph("<b>Dimension</b>", self.styles["score_label"]),
            Paragraph("<b>Score</b>", self.styles["score_value"]),
            Paragraph("<b>Rating</b>", self.styles["score_label"]),
        ]

        rows = [header]
        for name, score in dimensions:
            color = _score_color(score)
            score_text = f"{score}/5" if score is not None else "—"
            rows.append([
                Paragraph(_safe(name), self.styles["score_label"]),
                Paragraph(
                    f'<font color="#{color.hexval()[2:]}">{score_text}</font>',
                    self.styles["score_value"],
                ),
                Paragraph(
                    f'<font color="#{color.hexval()[2:]}">{_score_label(score)}</font>',
                    self.styles["score_label"],
                ),
            ])

        # Average row
        avg_str = f"{average_score}/5" if average_score is not None else "—"
        avg_color = _score_color(int(average_score) if average_score else None)
        rows.append([
            Paragraph("<b>Average Score</b>", self.styles["score_label"]),
            Paragraph(
                f'<b><font color="#{avg_color.hexval()[2:]}">{avg_str}</font></b>',
                self.styles["score_value"],
            ),
            Paragraph("", self.styles["score_label"]),
        ])

        table = Table(rows, colWidths=[3.8 * inch, 1.0 * inch, 1.8 * inch])
        table.setStyle(
            TableStyle([
                # Header
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                # Alternating rows
                *[
                    ("BACKGROUND", (0, i), (-1, i), BRAND_LIGHT_BG)
                    for i in range(2, len(rows), 2)
                ],
                # Average row highlight
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#edf2f7")),
                ("LINEABOVE", (0, -1), (-1, -1), 1, BRAND_PRIMARY),
                # Grid
                ("GRID", (0, 0), (-1, -1), 0.5, BRAND_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        story.append(table)
        story.append(Spacer(1, 12))

    def _render_star_analysis(self, story: list, sections: dict):
        """Render the STAR-by-STAR analysis sections."""
        story.append(Paragraph("STAR-by-STAR Analysis", self.styles["h2"]))

        analysis_text = sections.get("star_analysis", "")
        if not analysis_text:
            story.append(Paragraph("No detailed analysis available.", self.styles["body"]))
            return

        # Parse markdown sections
        for component in ["SITUATION", "TASK", "ACTION", "RESULT"]:
            pattern = rf"####?\s*{component}(.*?)(?=####?\s*[A-Z]|$)"
            match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                story.append(Paragraph(component.title(), self.styles["h3"]))
                self._render_markdown_block(story, content)

    def _render_company_alignment(
        self, story: list, alignment: dict, company_name: str
    ):
        """Render the company culture alignment section."""
        story.append(
            Paragraph(f"{company_name} Culture Alignment", self.styles["h2"])
        )

        aligned = alignment.get("aligned_principles", [])
        if aligned:
            story.append(
                Paragraph("Aligned Principles:", self.styles["strength_label"])
            )
            for principle in aligned:
                story.append(
                    Paragraph(f"&bull; {_safe(principle)}", self.styles["bullet"])
                )

        reinforce = alignment.get("reinforce_areas", [])
        if reinforce:
            story.append(Spacer(1, 4))
            story.append(
                Paragraph("Areas to Reinforce:", self.styles["opportunity_label"])
            )
            for area in reinforce:
                story.append(
                    Paragraph(f"&bull; {_safe(area)}", self.styles["bullet"])
                )

        if not aligned and not reinforce:
            story.append(
                Paragraph("See full evaluation for alignment details.", self.styles["body"])
            )

    def _render_follow_up_questions(self, story: list, questions: list[dict]):
        """Render predicted follow-up questions."""
        story.append(
            Paragraph("Follow-Up Questions to Expect", self.styles["h2"])
        )

        for i, q in enumerate(questions[:7], 1):
            q_text = q.get("question", "")
            if q_text:
                story.append(
                    Paragraph(f"<b>{i}.</b> {_safe(q_text)}", self.styles["body"])
                )
                why = q.get("why_asked", "")
                if why:
                    story.append(
                        Paragraph(
                            f"<i>Why:</i> {_safe(why)}",
                            self.styles["bullet"],
                        )
                    )
                how = q.get("how_to_prepare", "")
                if how:
                    story.append(
                        Paragraph(
                            f"<i>Prepare:</i> {_safe(how)}",
                            self.styles["bullet"],
                        )
                    )
                story.append(Spacer(1, 4))

    def _render_interview_readiness(self, story: list, readiness_text: str):
        """Render the interview readiness assessment and top priorities."""
        story.append(
            Paragraph("Interview Readiness Assessment", self.styles["h2"])
        )
        self._render_markdown_block(story, readiness_text)

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _render_markdown_block(self, story: list, text: str):
        """Render a block of markdown-ish text as paragraphs and bullets."""
        if not text:
            return

        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip section headers (we render our own)
            if line.startswith("###") or line.startswith("##"):
                continue

            # Bold labels: **Strengths:** or **Opportunities:**
            if line.startswith("**") and ":**" in line:
                # Extract the label and content
                label_match = re.match(r"\*\*(.*?)\*\*:?\s*(.*)", line)
                if label_match:
                    label = label_match.group(1)
                    content = label_match.group(2)

                    if any(
                        w in label.lower()
                        for w in ["strength", "worked", "good", "align"]
                    ):
                        style = self.styles["strength_label"]
                    elif any(
                        w in label.lower()
                        for w in ["opportunit", "improve", "reinforce", "develop"]
                    ):
                        style = self.styles["opportunity_label"]
                    else:
                        style = self.styles["body"]

                    story.append(Paragraph(f"<b>{_safe(label)}:</b>", style))
                    if content:
                        story.append(Paragraph(_safe(content), self.styles["body"]))
                    continue

            # Bullet points
            if line.startswith("- ") or line.startswith("* "):
                content = line[2:].strip()
                # Handle **bold** within bullets
                content = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", content)
                story.append(
                    Paragraph(f"&bull; {_safe(content)}", self.styles["bullet"])
                )
                continue

            # Numbered items
            num_match = re.match(r"(\d+)\.\s+(.*)", line)
            if num_match:
                content = num_match.group(2)
                content = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", content)
                story.append(
                    Paragraph(
                        f"<b>{num_match.group(1)}.</b> {_safe(content)}",
                        self.styles["body"],
                    )
                )
                continue

            # Regular paragraph
            clean = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", line)
            story.append(Paragraph(_safe(clean), self.styles["body"]))

    @staticmethod
    def _add_page_number(canvas, doc):
        """Add page numbers to each page."""
        page_num = canvas.getPageNumber()
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#718096"))
        canvas.drawCentredString(
            letter[0] / 2, 0.4 * inch, f"Page {page_num}"
        )
        canvas.restoreState()
