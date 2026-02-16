/**
 * Visual score indicator component.
 *
 * Renders a horizontal bar showing a 1-5 score with:
 * - Color coding (green = 4-5, amber = 3, red = 1-2)
 * - Label and numeric score with qualitative tag
 * - Proportional fill width with smooth animation
 */

import React from "react";
import { Box, Stack, Typography } from "@mui/material";

interface ScoreBarProps {
  label: string;
  score: number | null;
  maxScore?: number;
}

function getScoreColor(score: number): string {
  if (score >= 4) return "#38a169"; // Green — strong
  if (score >= 3) return "#d69e2e"; // Amber — solid
  return "#e53e3e"; // Red — needs work
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
      <Box sx={{ mb: 2 }}>
        <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.75 }}>
          <Typography variant="body2" fontWeight={500}>
            {label}
          </Typography>
          <Typography variant="body2" color="text.disabled">
            &mdash;
          </Typography>
        </Stack>
        <Box
          sx={{
            height: 8,
            borderRadius: 4,
            bgcolor: "grey.100",
          }}
        />
      </Box>
    );
  }

  const pct = (score / maxScore) * 100;
  const color = getScoreColor(score);
  const qualLabel = getScoreLabel(score);

  return (
    <Box sx={{ mb: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="baseline" sx={{ mb: 0.75 }}>
        <Typography variant="body2" fontWeight={500}>
          {label}
        </Typography>
        <Stack direction="row" alignItems="baseline" spacing={0.75}>
          <Typography variant="body2" fontWeight={700} sx={{ color }}>
            {score}/{maxScore}
          </Typography>
          {qualLabel && (
            <Typography variant="caption" sx={{ color, fontWeight: 500 }}>
              {qualLabel}
            </Typography>
          )}
        </Stack>
      </Stack>
      <Box
        sx={{
          height: 8,
          borderRadius: 4,
          bgcolor: "grey.100",
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
            height: "100%",
            width: `${pct}%`,
            borderRadius: 4,
            bgcolor: color,
            transition: "width 0.8s cubic-bezier(0.4, 0, 0.2, 1)",
          }}
        />
      </Box>
    </Box>
  );
}
