/**
 * Agentic Evaluation View — displays agentic evaluation results.
 *
 * Features:
 * - Radar chart for 4-dimension scores (0-100)
 * - Hiring decision badge (STRONG_HIRE, HIRE, BORDERLINE, REJECT)
 * - "The Diff" — side-by-side comparison of user answer vs Staff Engineer rewrite
 * - Red flags / missing components list
 * - Summary feedback
 *
 * This component renders within the existing EvaluationDetail page
 * when evaluation_type === "agentic".
 */

import React, { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Collapse,
  Divider,
  Grid,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import StarIcon from "@mui/icons-material/Star";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import PersonIcon from "@mui/icons-material/Person";

import type { Evaluation } from "../api/client";

// ---------------------------------------------------------------------------
// Dimension display names
// ---------------------------------------------------------------------------

const BEHAVIORAL_DIMENSIONS: Record<string, string> = {
  agentic_thinking: "Agentic Thinking",
  safety_alignment: "Safety & Alignment",
  engineering_rigor: "Engineering Rigor",
  communication: "Communication",
};

const SYSTEM_DESIGN_DIMENSIONS: Record<string, string> = {
  requirements_clarity: "Requirements & Scope",
  architecture_soundness: "Architecture Soundness",
  agentic_patterns: "Agentic Patterns",
  safety_security: "Safety & Security",
};

function getDimensionLabels(scores: Record<string, number>): Record<string, string> {
  const keys = Object.keys(scores);
  if (keys.includes("agentic_thinking")) return BEHAVIORAL_DIMENSIONS;
  if (keys.includes("requirements_clarity")) return SYSTEM_DESIGN_DIMENSIONS;
  // Fallback: use the key itself, title-cased
  const result: Record<string, string> = {};
  for (const key of keys) {
    result[key] = key
      .split("_")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ");
  }
  return result;
}

// ---------------------------------------------------------------------------
// Score color logic (0-100 scale)
// ---------------------------------------------------------------------------

function getScoreColor100(score: number): string {
  if (score >= 80) return "#38a169"; // Green — strong
  if (score >= 65) return "#d69e2e"; // Amber — solid
  if (score >= 50) return "#dd6b20"; // Orange — borderline
  return "#e53e3e"; // Red — weak
}

function getScoreLabel100(score: number): string {
  if (score >= 90) return "Exceptional";
  if (score >= 80) return "Strong";
  if (score >= 70) return "Solid";
  if (score >= 60) return "Average";
  if (score >= 50) return "Below Avg";
  return "Weak";
}

// ---------------------------------------------------------------------------
// Hiring decision styling
// ---------------------------------------------------------------------------

function getHiringDecisionStyle(decision: string): {
  color: string;
  bgcolor: string;
  icon: React.ReactNode;
} {
  switch (decision) {
    case "STRONG_HIRE":
      return {
        color: "#1b5e20",
        bgcolor: "#c8e6c9",
        icon: <StarIcon sx={{ color: "#1b5e20" }} />,
      };
    case "HIRE":
      return {
        color: "#2e7d32",
        bgcolor: "#e8f5e9",
        icon: <CheckCircleOutlineIcon sx={{ color: "#2e7d32" }} />,
      };
    case "BORDERLINE":
      return {
        color: "#e65100",
        bgcolor: "#fff3e0",
        icon: <WarningAmberIcon sx={{ color: "#e65100" }} />,
      };
    case "REJECT":
      return {
        color: "#b71c1c",
        bgcolor: "#ffebee",
        icon: <ErrorOutlineIcon sx={{ color: "#b71c1c" }} />,
      };
    default:
      return {
        color: "#616161",
        bgcolor: "#f5f5f5",
        icon: null,
      };
  }
}

// ---------------------------------------------------------------------------
// Score Bar for 0-100 scale
// ---------------------------------------------------------------------------

function AgenticScoreBar({
  label,
  score,
}: {
  label: string;
  score: number;
}) {
  const color = getScoreColor100(score);
  const scoreLabel = getScoreLabel100(score);

  return (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
        <Typography variant="body2" fontWeight={500}>
          {label}
        </Typography>
        <Typography variant="body2" fontWeight={600} sx={{ color }}>
          {score}/100 — {scoreLabel}
        </Typography>
      </Box>
      <Box
        sx={{
          height: 10,
          borderRadius: 5,
          bgcolor: "grey.200",
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
            height: "100%",
            width: `${score}%`,
            borderRadius: 5,
            bgcolor: color,
            transition: "width 0.8s ease",
          }}
        />
      </Box>
    </Box>
  );
}

// ---------------------------------------------------------------------------
// CSS Radar Chart (no charting library needed)
// ---------------------------------------------------------------------------

function RadarChart({
  scores,
  labels,
}: {
  scores: Record<string, number>;
  labels: Record<string, string>;
}) {
  const dimensions = Object.keys(scores);
  const n = dimensions.length;
  if (n < 3) return null;

  const size = 200;
  const center = size / 2;
  const maxRadius = size / 2 - 20;

  // Calculate polygon points for the score shape
  const scorePoints = dimensions.map((dim, i) => {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2;
    const radius = (scores[dim] / 100) * maxRadius;
    return {
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle),
    };
  });

  // Grid rings at 25%, 50%, 75%, 100%
  const rings = [0.25, 0.5, 0.75, 1.0];

  // Axis lines
  const axes = dimensions.map((_, i) => {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2;
    return {
      x2: center + maxRadius * Math.cos(angle),
      y2: center + maxRadius * Math.sin(angle),
    };
  });

  // Label positions (slightly outside the chart)
  const labelPositions = dimensions.map((dim, i) => {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2;
    const labelRadius = maxRadius + 16;
    return {
      x: center + labelRadius * Math.cos(angle),
      y: center + labelRadius * Math.sin(angle),
      label: labels[dim] || dim,
      score: scores[dim],
    };
  });

  const scorePolygon = scorePoints.map((p) => `${p.x},${p.y}`).join(" ");

  return (
    <Box sx={{ textAlign: "center", my: 2 }}>
      <svg
        viewBox={`-30 -30 ${size + 60} ${size + 60}`}
        width="100%"
        style={{ maxWidth: 300 }}
      >
        {/* Grid rings */}
        {rings.map((r) => {
          const ringPoints = dimensions.map((_, i) => {
            const angle = (2 * Math.PI * i) / n - Math.PI / 2;
            const radius = r * maxRadius;
            return `${center + radius * Math.cos(angle)},${
              center + radius * Math.sin(angle)
            }`;
          });
          return (
            <polygon
              key={r}
              points={ringPoints.join(" ")}
              fill="none"
              stroke="#e0e0e0"
              strokeWidth={0.5}
            />
          );
        })}

        {/* Axis lines */}
        {axes.map((axis, i) => (
          <line
            key={i}
            x1={center}
            y1={center}
            x2={axis.x2}
            y2={axis.y2}
            stroke="#e0e0e0"
            strokeWidth={0.5}
          />
        ))}

        {/* Score polygon — uses theme navy */}
        <polygon
          points={scorePolygon}
          fill="rgba(26, 54, 93, 0.15)"
          stroke="#1a365d"
          strokeWidth={2}
          strokeLinejoin="round"
        />

        {/* Score dots */}
        {scorePoints.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={4}
            fill="#1a365d"
            stroke="white"
            strokeWidth={1.5}
          />
        ))}

        {/* Labels */}
        {labelPositions.map((lp, i) => (
          <text
            key={i}
            x={lp.x}
            y={lp.y}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={9}
            fontFamily="system-ui, sans-serif"
            fill="#424242"
          >
            <tspan x={lp.x} dy="-0.5em" fontWeight={600}>
              {lp.label}
            </tspan>
            <tspan
              x={lp.x}
              dy="1.2em"
              fill={getScoreColor100(lp.score)}
              fontWeight={700}
            >
              {lp.score}
            </tspan>
          </text>
        ))}
      </svg>
    </Box>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

interface AgenticEvaluationViewProps {
  evaluation: Evaluation;
}

export default function AgenticEvaluationView({
  evaluation,
}: AgenticEvaluationViewProps) {
  const scores = evaluation.agentic_scores;
  const result = evaluation.agentic_result;

  if (!scores || !result) {
    return (
      <Alert severity="warning">
        Agentic evaluation data is not available.
      </Alert>
    );
  }

  const labels = getDimensionLabels(scores);
  const avgScore = Math.round(
    Object.values(scores).reduce((a, b) => a + b, 0) / Object.values(scores).length
  );
  const hiringDecision = evaluation.hiring_decision || result.hiring_decision || "—";
  const decisionStyle = getHiringDecisionStyle(hiringDecision);

  const feedback = result.summary_feedback || result.feedback_summary || "";
  const redFlags = result.red_flags || [];
  const missingComponents = result.missing_components || [];
  const theDiff = result.the_diff || {};

  return (
    <Grid container spacing={3}>
      {/* Left Panel — Scores + Decision */}
      <Grid item xs={12} md={4}>
        <Card sx={{ position: "sticky", top: 80 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Agentic Scores
            </Typography>

            {/* Hiring Decision Badge */}
            <Paper
              elevation={0}
              sx={{
                textAlign: "center",
                py: 2.5,
                mb: 2.5,
                bgcolor: decisionStyle.bgcolor,
                borderRadius: 2,
                border: 1,
                borderColor: decisionStyle.color,
                borderStyle: "solid",
                opacity: 0.95,
              }}
            >
              <Stack direction="row" justifyContent="center" alignItems="center" spacing={1}>
                {decisionStyle.icon}
                <Typography
                  variant="h5"
                  fontWeight={800}
                  sx={{ color: decisionStyle.color, letterSpacing: "-0.01em" }}
                >
                  {hiringDecision.replace(/_/g, " ")}
                </Typography>
              </Stack>
              <Typography
                variant="body2"
                sx={{ color: decisionStyle.color, mt: 0.5, fontWeight: 600 }}
              >
                {avgScore}/100 average
              </Typography>
            </Paper>

            {/* Radar Chart */}
            <RadarChart scores={scores} labels={labels} />

            <Divider sx={{ my: 2 }} />

            {/* Score Bars */}
            {Object.entries(scores).map(([dim, score]) => (
              <AgenticScoreBar
                key={dim}
                label={labels[dim] || dim}
                score={score}
              />
            ))}
          </CardContent>
        </Card>

        {/* Red Flags */}
        {redFlags.length > 0 && (
          <Card sx={{ mt: 2, border: 1, borderColor: "error.light" }}>
            <CardContent>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                <ErrorOutlineIcon color="error" />
                <Typography variant="h6" color="error.dark">
                  Red Flags
                </Typography>
              </Stack>
              {redFlags.map((flag, i) => (
                <Alert
                  key={i}
                  severity="error"
                  variant="outlined"
                  sx={{ mb: 1, "&:last-child": { mb: 0 } }}
                >
                  {flag}
                </Alert>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Missing Components (system design) */}
        {missingComponents.length > 0 && (
          <Card sx={{ mt: 2, border: 1, borderColor: "warning.light" }}>
            <CardContent>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                <WarningAmberIcon color="warning" />
                <Typography variant="h6" color="warning.dark">
                  Missing Components
                </Typography>
              </Stack>
              {missingComponents.map((comp, i) => (
                <Alert
                  key={i}
                  severity="warning"
                  variant="outlined"
                  sx={{ mb: 1, "&:last-child": { mb: 0 } }}
                >
                  {comp}
                </Alert>
              ))}
            </CardContent>
          </Card>
        )}
      </Grid>

      {/* Right Panel — Feedback + The Diff */}
      <Grid item xs={12} md={8}>
        {/* Summary Feedback */}
        {feedback && (
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Feedback
              </Typography>
              <Typography variant="body1">{feedback}</Typography>
            </CardContent>
          </Card>
        )}

        {/* THE DIFF — the hero feature */}
        <Card
          sx={{
            mb: 2,
            border: 2,
            borderColor: "primary.main",
            overflow: "hidden",
          }}
        >
          {/* Diff header band */}
          <Box
            sx={{
              px: 3,
              py: 2,
              background: "linear-gradient(135deg, #1a365d 0%, #2b6cb0 100%)",
              color: "white",
            }}
          >
            <Stack direction="row" spacing={1.5} alignItems="center">
              <Typography variant="h5" fontWeight={800} sx={{ letterSpacing: "-0.01em" }}>
                The Diff
              </Typography>
              <Chip
                label="Key Takeaway"
                size="small"
                sx={{
                  bgcolor: "rgba(255,255,255,0.2)",
                  color: "white",
                  fontWeight: 600,
                  height: 24,
                }}
              />
            </Stack>
            <Typography variant="body2" sx={{ opacity: 0.85, mt: 0.5 }}>
              Your answer vs. what a Staff Engineer would say. This is the most valuable part of your evaluation.
            </Typography>
          </Box>
          <CardContent sx={{ pt: 2.5 }}>

            <Grid container spacing={2}>
              {/* User's Answer / Critique */}
              <Grid item xs={12} md={6}>
                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    bgcolor: "#fff3e0",
                    borderRadius: 2,
                    height: "100%",
                    borderLeft: 4,
                    borderColor: "#e65100",
                  }}
                >
                  <Typography
                    variant="subtitle2"
                    fontWeight={700}
                    color="#e65100"
                    gutterBottom
                  >
                    {theDiff.user_answer_critique
                      ? "YOUR ANSWER — CRITIQUE"
                      : "YOUR APPROACH"}
                  </Typography>
                  <Typography variant="body2">
                    {theDiff.user_answer_critique ||
                      theDiff.candidate_approach ||
                      "No critique available."}
                  </Typography>
                </Paper>
              </Grid>

              {/* Staff Engineer Rewrite */}
              <Grid item xs={12} md={6}>
                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    bgcolor: "#e8f5e9",
                    borderRadius: 2,
                    height: "100%",
                    borderLeft: 4,
                    borderColor: "#2e7d32",
                  }}
                >
                  <Typography
                    variant="subtitle2"
                    fontWeight={700}
                    color="#2e7d32"
                    gutterBottom
                  >
                    {theDiff.staff_engineer_rewrite
                      ? "STAFF ENGINEER ANSWER"
                      : "STAFF ARCHITECT APPROACH"}
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{ whiteSpace: "pre-wrap" }}
                  >
                    {theDiff.staff_engineer_rewrite ||
                      theDiff.staff_architect_approach ||
                      "No rewrite available."}
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Collapsible: View My Original Answer */}
        {evaluation.answer_text && (
          <OriginalAnswerSection answerText={evaluation.answer_text} />
        )}
      </Grid>
    </Grid>
  );
}

// ---------------------------------------------------------------------------
// Original Answer — collapsible comparison
// ---------------------------------------------------------------------------

function OriginalAnswerSection({ answerText }: { answerText: string }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card variant="outlined" sx={{ mt: 2 }}>
      <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
        <Button
          fullWidth
          onClick={() => setExpanded(!expanded)}
          startIcon={<PersonIcon />}
          endIcon={
            <ExpandMoreIcon
              sx={{
                transform: expanded ? "rotate(180deg)" : "rotate(0deg)",
                transition: "transform 0.2s",
              }}
            />
          }
          sx={{
            justifyContent: "space-between",
            textTransform: "none",
            fontWeight: 600,
            color: "text.primary",
          }}
        >
          View My Original Answer
        </Button>
        <Collapse in={expanded}>
          <Paper
            elevation={0}
            sx={{
              mt: 1.5,
              p: 2,
              bgcolor: "action.hover",
              borderRadius: 2,
              border: 1,
              borderColor: "divider",
            }}
          >
            <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
              {answerText}
            </Typography>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: "block", mt: 1 }}
            >
              {answerText.trim().split(/\s+/).length} words
            </Typography>
          </Paper>
        </Collapse>
      </CardContent>
    </Card>
  );
}
