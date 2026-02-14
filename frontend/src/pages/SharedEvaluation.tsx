/**
 * Public shared evaluation view — read-only, no auth required.
 *
 * Shows scores, feedback, company alignment, and follow-up questions.
 * Intentionally excludes: answer text, user info, coach notes.
 *
 * Accessed via /shared/:token — the token is a UUID that maps to an
 * evaluation's share_token column.
 */

import React from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import ShareIcon from "@mui/icons-material/Share";

import { getSharedEvaluation } from "../api/client";
import ScoreBar from "../components/ScoreBar";
import SimpleMarkdown from "../components/SimpleMarkdown";
import PageLoader from "../components/PageLoader";

export default function SharedEvaluation() {
  const { token } = useParams<{ token: string }>();

  const {
    data: evaluation,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["shared-evaluation", token],
    queryFn: () => getSharedEvaluation(token!),
    enabled: !!token,
  });

  if (isLoading) {
    return <PageLoader message="Loading shared evaluation..." />;
  }

  if (error) {
    return (
      <Box sx={{ maxWidth: 600, mx: "auto", py: 4 }}>
        <Alert severity="error">
          This shared evaluation link is invalid or has expired.
        </Alert>
      </Box>
    );
  }

  if (!evaluation) {
    return (
      <Box sx={{ maxWidth: 600, mx: "auto", py: 4 }}>
        <Alert severity="warning">Evaluation not found.</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 900, mx: "auto" }}>
      {/* Header */}
      <Stack spacing={1} sx={{ mb: 3 }}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <ShareIcon color="primary" />
          <Typography variant="overline" color="primary">
            Shared Evaluation
          </Typography>
        </Stack>
        <Typography
          variant="h4"
          sx={{ fontSize: { xs: "1.4rem", sm: "2.125rem" } }}
        >
          STAR Evaluation Results
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap">
          {evaluation.company_name && (
            <Chip label={evaluation.company_name} size="small" />
          )}
          {evaluation.target_role && (
            <Chip
              label={evaluation.target_role}
              size="small"
              variant="outlined"
            />
          )}
          <Chip
            label={new Date(evaluation.created_at).toLocaleDateString()}
            size="small"
            variant="outlined"
          />
        </Stack>
        {evaluation.question_text && (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ fontStyle: "italic" }}
          >
            &ldquo;{evaluation.question_text}&rdquo;
          </Typography>
        )}
      </Stack>

      <Grid container spacing={3}>
        {/* Score Panel */}
        <Grid item xs={12} md={4}>
          <Card sx={{ position: "sticky", top: 80 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Dimension Scores
              </Typography>

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

          {/* Footer */}
          <Box sx={{ textAlign: "center", py: 3 }}>
            <Typography variant="caption" color="text.secondary">
              Generated by BIAE — Behavioral Interview Answer Evaluator
            </Typography>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
}
