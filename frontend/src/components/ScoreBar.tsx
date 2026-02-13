/**
 * Visual score indicator component.
 *
 * Renders a horizontal bar showing a 1-5 score with:
 * - Color coding (green = 4-5, amber = 3, red = 1-2)
 * - Label and numeric score
 * - Proportional fill width
 */

import React from "react";
import { Box, Typography } from "@mui/material";

interface ScoreBarProps {
  label: string;
  score: number | null;
  maxScore?: number;
}

function getScoreColor(score: number): string {
  if (score >= 4) return "#38a169"; // Green
  if (score >= 3) return "#d69e2e"; // Amber
  return "#e53e3e"; // Red
}

function getScoreLabel(score: number): string {
  const labels: Record<number, string> = {
    5: "Exceptional",
    4: "Strong",
    3: "Solid",
    2: "Needs Work",
    1: "Off-Track",
  };
  return labels[score] || "";
}

export default function ScoreBar({
  label,
  score,
  maxScore = 5,
}: ScoreBarProps) {
  if (score === null) {
    return (
      <Box sx={{ mb: 1.5 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
          <Typography variant="body2" fontWeight={500}>
            {label}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            —
          </Typography>
        </Box>
        <Box
          sx={{
            height: 8,
            borderRadius: 4,
            bgcolor: "grey.200",
          }}
        />
      </Box>
    );
  }

  const pct = (score / maxScore) * 100;
  const color = getScoreColor(score);

  return (
    <Box sx={{ mb: 1.5 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
        <Typography variant="body2" fontWeight={500}>
          {label}
        </Typography>
        <Typography variant="body2" fontWeight={600} sx={{ color }}>
          {score}/{maxScore} — {getScoreLabel(score)}
        </Typography>
      </Box>
      <Box
        sx={{
          height: 8,
          borderRadius: 4,
          bgcolor: "grey.200",
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
            height: "100%",
            width: `${pct}%`,
            borderRadius: 4,
            bgcolor: color,
            transition: "width 0.6s ease",
          }}
        />
      </Box>
    </Box>
  );
}
