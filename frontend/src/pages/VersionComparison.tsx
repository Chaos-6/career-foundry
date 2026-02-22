/**
 * Version Comparison page — side-by-side score tracking across answer revisions.
 *
 * Shows:
 * - Score summary cards for each version (with deltas highlighted)
 * - Score trend visualization (which dimensions improved/declined)
 * - Quick link to view each version's full evaluation
 *
 * The backend's /answers/{id}/compare endpoint returns all versions with
 * their latest evaluation scores, making this mostly a rendering exercise.
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
  Divider,
  Grid,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import RemoveIcon from "@mui/icons-material/Remove";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import VisibilityIcon from "@mui/icons-material/Visibility";

import { getAnswerComparison, VersionScoreSummary } from "../api/client";
import AppBreadcrumbs from "../components/AppBreadcrumbs";
import PageLoader from "../components/PageLoader";

const DIMENSIONS = [
  { key: "situation_score", label: "Situation" },
  { key: "task_score", label: "Task" },
  { key: "action_score", label: "Action" },
  { key: "result_score", label: "Result" },
  { key: "engagement_score", label: "Engagement" },
  { key: "overall_score", label: "Overall" },
  { key: "average_score", label: "Average" },
] as const;

/** Render a delta indicator: green up arrow, red down arrow, or dash */
function DeltaIndicator({ current, previous }: { current: number | null; previous: number | null }) {
  if (current === null || previous === null) return null;

  const delta = Number(current) - Number(previous);

  if (delta > 0) {
    return (
      <Chip
        icon={<ArrowUpwardIcon sx={{ fontSize: 14 }} />}
        label={`+${delta.toFixed(1)}`}
        size="small"
        color="success"
        variant="outlined"
        sx={{ ml: 0.5, height: 22, "& .MuiChip-label": { px: 0.5 } }}
      />
    );
  }

  if (delta < 0) {
    return (
      <Chip
        icon={<ArrowDownwardIcon sx={{ fontSize: 14 }} />}
        label={delta.toFixed(1)}
        size="small"
        color="error"
        variant="outlined"
        sx={{ ml: 0.5, height: 22, "& .MuiChip-label": { px: 0.5 } }}
      />
    );
  }

  return (
    <Chip
      icon={<RemoveIcon sx={{ fontSize: 14 }} />}
      label="0"
      size="small"
      variant="outlined"
      sx={{ ml: 0.5, height: 22, "& .MuiChip-label": { px: 0.5 } }}
    />
  );
}

/** Color a score cell based on 1-5 scale */
function scoreColor(score: number | null): string {
  if (score === null) return "text.secondary";
  const s = Number(score);
  if (s >= 4) return "success.main";
  if (s >= 3) return "warning.main";
  return "error.main";
}

export default function VersionComparison() {
  const { answerId } = useParams<{ answerId: string }>();
  const navigate = useNavigate();

  const {
    data: comparison,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["answer-comparison", answerId],
    queryFn: () => getAnswerComparison(answerId!),
    enabled: !!answerId,
  });

  if (isLoading) {
    return <PageLoader message="Loading version comparison..." />;
  }

  if (error || !comparison) {
    return (
      <Alert severity="error">
        Failed to load comparison data. Please try again.
      </Alert>
    );
  }

  const versions = comparison.version_scores;
  const hasMultipleVersions = versions.length > 1;

  // Find best score per dimension for highlighting
  const bestScores: Record<string, number> = {};
  DIMENSIONS.forEach(({ key }) => {
    const scores = versions
      .map((v) => v[key as keyof VersionScoreSummary] as number | null)
      .filter((s): s is number => s !== null);
    if (scores.length > 0) {
      bestScores[key] = Math.max(...scores.map(Number));
    }
  });

  return (
    <Box sx={{ maxWidth: 960, mx: "auto" }}>
      <AppBreadcrumbs
        crumbs={[
          { label: "Dashboard", path: "/" },
          { label: "Compare Versions" },
        ]}
      />

      {/* Header */}
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 3 }}
      >
        <Box>
          <Typography
            variant="h4"
            gutterBottom
            sx={{ fontSize: { xs: "1.5rem", sm: "2.125rem" } }}
          >
            Version Comparison
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {comparison.target_role} &bull; {comparison.experience_level} &bull;{" "}
            {versions.length} version{versions.length !== 1 ? "s" : ""}
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(-1)}
        >
          Back
        </Button>
      </Stack>

      {/* Improvement Summary */}
      {hasMultipleVersions && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Improvement Summary
            </Typography>
            <ImprovementSummary versions={versions} />
          </CardContent>
        </Card>
      )}

      {/* Score Comparison Table */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Scores by Version
          </Typography>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 600 }}>Dimension</TableCell>
                  {versions.map((v) => (
                    <TableCell key={v.id} align="center" sx={{ fontWeight: 600 }}>
                      v{v.version_number}
                      {v.is_ai_assisted && (
                        <Chip
                          label="AI"
                          size="small"
                          sx={{ ml: 0.5, height: 18, fontSize: 10 }}
                        />
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {DIMENSIONS.map(({ key, label }) => (
                  <TableRow key={key}>
                    <TableCell sx={{ fontWeight: 500 }}>{label}</TableCell>
                    {versions.map((v, idx) => {
                      const score = v[key as keyof VersionScoreSummary] as
                        | number
                        | null;
                      const prevScore =
                        idx > 0
                          ? (versions[idx - 1][
                              key as keyof VersionScoreSummary
                            ] as number | null)
                          : null;
                      const isBest =
                        score !== null && Number(score) === bestScores[key];

                      return (
                        <TableCell key={v.id} align="center">
                          <Stack
                            direction="row"
                            justifyContent="center"
                            alignItems="center"
                          >
                            <Typography
                              variant="body2"
                              fontWeight={isBest ? 700 : 400}
                              color={scoreColor(score)}
                            >
                              {score !== null ? Number(score).toFixed(key === "average_score" ? 1 : 0) : "—"}
                            </Typography>
                            {idx > 0 && (
                              <DeltaIndicator
                                current={score}
                                previous={prevScore}
                              />
                            )}
                          </Stack>
                        </TableCell>
                      );
                    })}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Version Cards */}
      <Typography variant="h6" gutterBottom>
        Version Details
      </Typography>
      <Grid container spacing={2}>
        {versions.map((v) => (
          <Grid item xs={12} sm={6} key={v.id}>
            <Card
              sx={{
                height: "100%",
                border:
                  v.version_number === versions.length ? 2 : 0,
                borderColor: "secondary.main",
              }}
            >
              <CardContent>
                <Stack
                  direction="row"
                  justifyContent="space-between"
                  alignItems="center"
                  sx={{ mb: 1 }}
                >
                  <Typography variant="h6">
                    Version {v.version_number}
                  </Typography>
                  <Stack direction="row" spacing={0.5}>
                    {v.version_number === versions.length && (
                      <Chip label="Latest" size="small" color="secondary" />
                    )}
                    {v.is_ai_assisted && (
                      <Chip
                        label="AI-Assisted"
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </Stack>
                </Stack>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {v.word_count ?? "?"} words &bull;{" "}
                  {new Date(v.created_at).toLocaleDateString()}
                </Typography>

                {v.average_score !== null ? (
                  <Typography
                    variant="h4"
                    fontWeight={700}
                    color={scoreColor(v.average_score)}
                    sx={{ my: 1 }}
                  >
                    {Number(v.average_score).toFixed(1)}
                    <Typography
                      component="span"
                      variant="body2"
                      color="text.secondary"
                    >
                      /5
                    </Typography>
                  </Typography>
                ) : (
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ my: 1 }}
                  >
                    {v.evaluation_status === "queued" ||
                    v.evaluation_status === "analyzing"
                      ? "Evaluating..."
                      : "Not evaluated"}
                  </Typography>
                )}

                <Divider sx={{ my: 1 }} />

                {v.evaluation_id && (
                  <Button
                    size="small"
                    startIcon={<VisibilityIcon />}
                    onClick={() =>
                      navigate(`/evaluations/${v.evaluation_id}`)
                    }
                  >
                    View Full Evaluation
                  </Button>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}

/**
 * Summary component showing the overall improvement trajectory.
 * Compares first version to latest version.
 */
function ImprovementSummary({
  versions,
}: {
  versions: VersionScoreSummary[];
}) {
  const first = versions[0];
  const latest = versions[versions.length - 1];

  if (!first || !latest) return null;
  if (first.average_score === null || latest.average_score === null) {
    return (
      <Typography variant="body2" color="text.secondary">
        Scores are not yet available for comparison.
      </Typography>
    );
  }

  const delta = Number(latest.average_score) - Number(first.average_score);
  const improved = delta > 0;
  const unchanged = delta === 0;

  return (
    <Stack direction="row" spacing={3} alignItems="center">
      <Box sx={{ textAlign: "center" }}>
        <Typography variant="caption" color="text.secondary">
          v1 Average
        </Typography>
        <Typography variant="h5" fontWeight={600}>
          {Number(first.average_score).toFixed(1)}
        </Typography>
      </Box>

      <Typography variant="h4" color="text.secondary">
        →
      </Typography>

      <Box sx={{ textAlign: "center" }}>
        <Typography variant="caption" color="text.secondary">
          v{latest.version_number} Average
        </Typography>
        <Typography variant="h5" fontWeight={600}>
          {Number(latest.average_score).toFixed(1)}
        </Typography>
      </Box>

      <Chip
        label={
          unchanged
            ? "No change"
            : `${improved ? "+" : ""}${delta.toFixed(1)} points`
        }
        color={improved ? "success" : unchanged ? "default" : "error"}
        sx={{ fontWeight: 600, fontSize: 14, height: 32 }}
      />
    </Stack>
  );
}
