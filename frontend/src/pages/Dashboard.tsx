/**
 * Dashboard page — landing hub with all features.
 *
 * Shows:
 * - 4 feature cards (Evaluate, Mock Interview, AI Generator, Question Bank)
 * - "How It Works" explainer
 */

import React from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import RateReviewIcon from "@mui/icons-material/RateReview";
import QuizIcon from "@mui/icons-material/Quiz";
import TimerIcon from "@mui/icons-material/Timer";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";

const features = [
  {
    path: "/evaluate",
    label: "New Evaluation",
    icon: <RateReviewIcon sx={{ fontSize: 40, color: "primary.main" }} />,
    desc: "Paste your STAR answer and get scored feedback across 6 dimensions with company-specific alignment analysis.",
    buttonLabel: "Start Evaluation",
    buttonVariant: "contained" as const,
    color: "primary" as const,
  },
  {
    path: "/mock",
    label: "Mock Interview",
    icon: <TimerIcon sx={{ fontSize: 40, color: "error.main" }} />,
    desc: "Practice under time pressure. Get a random question, countdown timer, and automatic evaluation when time runs out.",
    buttonLabel: "Start Mock",
    buttonVariant: "outlined" as const,
    color: "error" as const,
  },
  {
    path: "/generator",
    label: "AI Generator",
    icon: <AutoAwesomeIcon sx={{ fontSize: 40, color: "secondary.main" }} />,
    desc: "Enter bullet points for each STAR component and let AI draft a polished narrative. Edit, then evaluate.",
    buttonLabel: "Generate Answer",
    buttonVariant: "outlined" as const,
    color: "secondary" as const,
  },
  {
    path: "/questions",
    label: "Question Bank",
    icon: <QuizIcon sx={{ fontSize: 40, color: "info.main" }} />,
    desc: "Browse 80+ behavioral interview questions filtered by role, competency, and difficulty.",
    buttonLabel: "Browse Questions",
    buttonVariant: "outlined" as const,
    color: "info" as const,
  },
];

const steps = [
  {
    num: "1",
    title: "Context",
    desc: "Select your target company (22+ with researched guiding principles), role, and experience level.",
  },
  {
    num: "2",
    title: "Question",
    desc: "Pick from the curated question bank or write your own behavioral question.",
  },
  {
    num: "3",
    title: "Answer",
    desc: "Write your STAR-formatted answer (Situation, Task, Action, Result).",
  },
  {
    num: "4",
    title: "Evaluate",
    desc: "Claude analyzes your answer across 6 dimensions, providing scored feedback and company alignment.",
  },
  {
    num: "5",
    title: "Improve",
    desc: "Download the PDF report, revise your answer, and re-evaluate to track improvement.",
  },
];

export default function Dashboard() {
  const navigate = useNavigate();

  return (
    <Box sx={{ maxWidth: 960, mx: "auto" }}>
      {/* Hero */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom fontWeight={700}>
          Welcome to BIAE
        </Typography>
        <Typography variant="h6" color="text.secondary" fontWeight={400}>
          AI-powered STAR answer coaching for tech interview preparation
        </Typography>
      </Box>

      {/* Feature cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {features.map((f) => (
          <Grid item xs={12} sm={6} key={f.path}>
            <Card
              sx={{
                height: "100%",
                cursor: "pointer",
                "&:hover": { boxShadow: 4, transform: "translateY(-2px)" },
                transition: "all 0.2s",
              }}
              onClick={() => navigate(f.path)}
            >
              <CardContent
                sx={{
                  display: "flex",
                  flexDirection: "column",
                  height: "100%",
                  p: 3,
                }}
              >
                <Box sx={{ mb: 2 }}>{f.icon}</Box>
                <Typography variant="h6" gutterBottom>
                  {f.label}
                </Typography>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 2, flexGrow: 1 }}
                >
                  {f.desc}
                </Typography>
                <Button
                  variant={f.buttonVariant}
                  color={f.color}
                  fullWidth
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(f.path);
                  }}
                >
                  {f.buttonLabel}
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* How It Works */}
      <Card>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom fontWeight={600}>
            How It Works
          </Typography>
          <Grid container spacing={2}>
            {steps.map((s) => (
              <Grid item xs={12} sm={6} md={4} key={s.num}>
                <Stack direction="row" spacing={1.5} alignItems="flex-start">
                  <CheckCircleOutlineIcon
                    color="secondary"
                    sx={{ mt: 0.3, flexShrink: 0 }}
                  />
                  <Box>
                    <Typography variant="subtitle2" fontWeight={600}>
                      {s.num}. {s.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {s.desc}
                    </Typography>
                  </Box>
                </Stack>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
}
