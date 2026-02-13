/**
 * Evaluation Detail page — shows scores and full feedback.
 *
 * Polls the evaluation status until it transitions to 'completed' or 'failed'.
 * Then renders:
 * - 6-dimension score bars
 * - Full evaluation markdown
 * - PDF download button
 * - "Revise & Re-Evaluate" button (placeholder for Milestone 6)
 */

import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";
import EditIcon from "@mui/icons-material/Edit";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";

import { getEvaluation, getEvaluationPdfUrl, Evaluation } from "../api/client";
import ScoreBar from "../components/ScoreBar";
import SimpleMarkdown from "../components/SimpleMarkdown";

export default function EvaluationDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const {
    data: evaluation,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["evaluation", id],
    queryFn: () => getEvaluation(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Poll every 2s while not completed/failed
      if (!data) return 2000;
      if (data.status === "completed" || data.status === "failed") return false;
      return 2000;
    },
  });

  if (isLoading) {
    return (
      <Box sx={{ textAlign: "center", py: 8 }}>
        <CircularProgress size={48} />
        <Typography sx={{ mt: 2 }} color="text.secondary">
          Loading evaluation...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load evaluation. Please try again.
      </Alert>
    );
  }

  if (!evaluation) {
    return <Alert severity="warning">Evaluation not found.</Alert>;
  }

  // --- In-progress states ---
  if (evaluation.status === "queued" || evaluation.status === "analyzing") {
    return (
      <Box sx={{ textAlign: "center", py: 8, maxWidth: 500, mx: "auto" }}>
        <CircularProgress size={64} thickness={3} />
        <Typography variant="h5" sx={{ mt: 3, mb: 1 }}>
          {evaluation.status === "queued"
            ? "Queued for Analysis..."
            : "Analyzing Your Answer..."}
        </Typography>
        <Typography color="text.secondary">
          {evaluation.status === "queued"
            ? "Your answer is queued. Analysis will begin shortly."
            : "Claude is evaluating your STAR answer across 6 dimensions. This typically takes 15-30 seconds."}
        </Typography>
        <Chip
          label={evaluation.status}
          color="primary"
          variant="outlined"
          sx={{ mt: 2 }}
        />
      </Box>
    );
  }

  // --- Failed state ---
  if (evaluation.status === "failed") {
    return (
      <Box sx={{ maxWidth: 600, mx: "auto" }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="subtitle1" fontWeight={600}>
            Evaluation Failed
          </Typography>
          <Typography variant="body2">
            {evaluation.error_message || "An unexpected error occurred."}
          </Typography>
        </Alert>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate("/evaluate")}
        >
          Try Again
        </Button>
      </Box>
    );
  }

  // --- Completed state ---
  return (
    <Box sx={{ maxWidth: 900, mx: "auto" }}>
      {/* Header */}
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 3 }}
      >
        <Box>
          <Typography variant="h4" gutterBottom>
            Evaluation Results
          </Typography>
          <Stack direction="row" spacing={1}>
            <Chip label={evaluation.model_used || "claude"} size="small" />
            {evaluation.processing_seconds && (
              <Chip
                label={`${evaluation.processing_seconds}s`}
                size="small"
                variant="outlined"
              />
            )}
            {evaluation.input_tokens && evaluation.output_tokens && (
              <Chip
                label={`${(
                  evaluation.input_tokens + evaluation.output_tokens
                ).toLocaleString()} tokens`}
                size="small"
                variant="outlined"
              />
            )}
          </Stack>
        </Box>
        <Stack direction="row" spacing={1}>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            href={getEvaluationPdfUrl(evaluation.id)}
            target="_blank"
          >
            Download PDF
          </Button>
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={() => navigate("/evaluate")}
          >
            New Evaluation
          </Button>
        </Stack>
      </Stack>

      <Grid container spacing={3}>
        {/* Score Panel */}
        <Grid item xs={12} md={4}>
          <Card sx={{ position: "sticky", top: 80 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Dimension Scores
              </Typography>

              {/* Average score highlight */}
              {evaluation.average_score !== null && (
                <Paper
                  elevation={0}
                  sx={{
                    textAlign: "center",
                    py: 2,
                    mb: 2,
                    bgcolor:
                      evaluation.average_score >= 4
                        ? "secondary.light"
                        : evaluation.average_score >= 3
                        ? "warning.light"
                        : "error.light",
                    borderRadius: 2,
                    color: "white",
                  }}
                >
                  <Typography variant="h3" fontWeight={700}>
                    {evaluation.average_score}
                  </Typography>
                  <Typography variant="caption">
                    Average Score (out of 5)
                  </Typography>
                </Paper>
              )}

              <ScoreBar
                label="Situation"
                score={evaluation.situation_score}
              />
              <ScoreBar label="Task" score={evaluation.task_score} />
              <ScoreBar label="Action" score={evaluation.action_score} />
              <ScoreBar label="Result" score={evaluation.result_score} />
              <ScoreBar
                label="Engagement"
                score={evaluation.engagement_score}
              />
              <Divider sx={{ my: 1 }} />
              <ScoreBar label="Overall" score={evaluation.overall_score} />
            </CardContent>
          </Card>

          {/* Company Alignment */}
          {evaluation.company_alignment && (
            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Company Alignment
                </Typography>
                {evaluation.company_alignment.aligned_principles?.length >
                  0 && (
                  <Box sx={{ mb: 1 }}>
                    <Typography
                      variant="caption"
                      color="secondary.main"
                      fontWeight={600}
                    >
                      ALIGNED
                    </Typography>
                    <Stack direction="row" flexWrap="wrap" gap={0.5}>
                      {evaluation.company_alignment.aligned_principles.map(
                        (p: string) => (
                          <Chip
                            key={p}
                            label={p}
                            size="small"
                            color="secondary"
                            variant="outlined"
                          />
                        )
                      )}
                    </Stack>
                  </Box>
                )}
                {evaluation.company_alignment.reinforce_areas?.length > 0 && (
                  <Box>
                    <Typography
                      variant="caption"
                      color="warning.main"
                      fontWeight={600}
                    >
                      REINFORCE
                    </Typography>
                    <Stack direction="row" flexWrap="wrap" gap={0.5}>
                      {evaluation.company_alignment.reinforce_areas.map(
                        (a: string) => (
                          <Chip
                            key={a}
                            label={a}
                            size="small"
                            color="warning"
                            variant="outlined"
                          />
                        )
                      )}
                    </Stack>
                  </Box>
                )}
              </CardContent>
            </Card>
          )}
        </Grid>

        {/* Full Evaluation */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Full Evaluation
              </Typography>
              {evaluation.evaluation_markdown ? (
                <SimpleMarkdown content={evaluation.evaluation_markdown} />
              ) : (
                <Typography color="text.secondary">
                  No evaluation content available.
                </Typography>
              )}
            </CardContent>
          </Card>

          {/* Follow-up Questions */}
          {evaluation.follow_up_questions &&
            evaluation.follow_up_questions.length > 0 && (
              <Card sx={{ mt: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Follow-Up Questions to Expect
                  </Typography>
                  {evaluation.follow_up_questions.map(
                    (q: any, i: number) => (
                      <Box key={i} sx={{ mb: 2 }}>
                        <Typography variant="body1" fontWeight={600}>
                          {i + 1}. {q.question}
                        </Typography>
                        {q.why_asked && (
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ ml: 2 }}
                          >
                            <em>Why:</em> {q.why_asked}
                          </Typography>
                        )}
                        {q.how_to_prepare && (
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ ml: 2 }}
                          >
                            <em>Prepare:</em> {q.how_to_prepare}
                          </Typography>
                        )}
                      </Box>
                    )
                  )}
                </CardContent>
              </Card>
            )}
        </Grid>
      </Grid>
    </Box>
  );
}
