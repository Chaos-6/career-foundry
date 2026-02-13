/**
 * Advanced Analytics page — competency radar chart, readiness score,
 * and per-company breakdowns.
 *
 * Shows:
 * - Interview Readiness gauge (weighted composite score)
 * - Competency Radar Chart (6 STAR dimensions)
 * - Per-company score breakdown table
 *
 * All data comes from a single /api/v1/dashboard/analytics endpoint
 * to minimise roundtrips. Requires authentication.
 */

import React from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
  LinearProgress,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";

import {
  getAnalytics,
  DimensionAverage,
  CompanyBreakdown,
  ReadinessScore,
} from "../api/client";

// ---------------------------------------------------------------------------
// Chart colours — consistent with Dashboard.tsx
// ---------------------------------------------------------------------------

const DIMENSION_COLORS: Record<string, string> = {
  Situation: "#38a169",
  Task: "#3182ce",
  Action: "#d69e2e",
  Result: "#805ad5",
  Engagement: "#e53e3e",
  Overall: "#1a365d",
};

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function Analytics() {
  const navigate = useNavigate();

  const {
    data: analytics,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["analytics"],
    queryFn: getAnalytics,
    staleTime: 60_000,
  });

  if (isLoading) {
    return (
      <Box sx={{ textAlign: "center", py: 8 }}>
        <CircularProgress size={48} />
        <Typography sx={{ mt: 2 }} color="text.secondary">
          Loading analytics...
        </Typography>
      </Box>
    );
  }

  if (error || !analytics) {
    return (
      <Alert severity="error">
        Failed to load analytics data. Make sure you have completed at least one
        evaluation.
      </Alert>
    );
  }

  const hasData = analytics.dimension_averages.some((d) => d.count > 0);

  return (
    <Box sx={{ maxWidth: 960, mx: "auto" }}>
      {/* Header */}
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 3 }}
      >
        <Box>
          <Typography variant="h4" gutterBottom fontWeight={700}>
            Advanced Analytics
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Competency profile, interview readiness, and per-company performance
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate("/")}
        >
          Dashboard
        </Button>
      </Stack>

      {!hasData ? (
        <Card>
          <CardContent sx={{ textAlign: "center", py: 6 }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No Evaluation Data Yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Complete at least one evaluation to see your analytics.
            </Typography>
            <Button
              variant="contained"
              onClick={() => navigate("/evaluate")}
            >
              Start Your First Evaluation
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {/* Readiness Score */}
          <Grid item xs={12} md={4}>
            <ReadinessGauge readiness={analytics.readiness} />
          </Grid>

          {/* Radar Chart */}
          <Grid item xs={12} md={8}>
            <Card sx={{ height: "100%" }}>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  Competency Profile
                </Typography>
                <CompetencyRadar dimensions={analytics.dimension_averages} />
              </CardContent>
            </Card>
          </Grid>

          {/* Dimension Breakdown Bars */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  Dimension Breakdown
                </Typography>
                <DimensionBars dimensions={analytics.dimension_averages} />
              </CardContent>
            </Card>
          </Grid>

          {/* Per-Company Breakdown */}
          {analytics.company_breakdowns.length > 0 && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom fontWeight={600}>
                    Performance by Company
                  </Typography>
                  <CompanyTable breakdowns={analytics.company_breakdowns} />
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )}
    </Box>
  );
}

// ---------------------------------------------------------------------------
// Readiness Gauge
// ---------------------------------------------------------------------------

function ReadinessGauge({
  readiness,
}: {
  readiness: ReadinessScore | null;
}) {
  if (!readiness) {
    return (
      <Card sx={{ height: "100%" }}>
        <CardContent sx={{ textAlign: "center", py: 4 }}>
          <Typography variant="body2" color="text.secondary">
            Need more evaluations to calculate readiness
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const gaugeColor =
    readiness.overall_readiness >= 80
      ? "success"
      : readiness.overall_readiness >= 60
      ? "secondary"
      : readiness.overall_readiness >= 40
      ? "warning"
      : "error";

  const components = [
    { label: "Score Quality", value: readiness.score_component, weight: "40%" },
    {
      label: "Consistency",
      value: readiness.consistency_component,
      weight: "30%",
    },
    {
      label: "Improvement Trend",
      value: readiness.trend_component,
      weight: "30%",
    },
  ];

  return (
    <Card sx={{ height: "100%" }}>
      <CardContent>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          Interview Readiness
        </Typography>

        {/* Central score */}
        <Box sx={{ textAlign: "center", my: 2 }}>
          <Box sx={{ position: "relative", display: "inline-flex" }}>
            <CircularProgress
              variant="determinate"
              value={readiness.overall_readiness}
              size={120}
              thickness={5}
              color={gaugeColor as any}
            />
            <Box
              sx={{
                position: "absolute",
                top: 0,
                left: 0,
                bottom: 0,
                right: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexDirection: "column",
              }}
            >
              <Typography variant="h4" fontWeight={700}>
                {readiness.overall_readiness}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                / 100
              </Typography>
            </Box>
          </Box>
          <Typography
            variant="subtitle1"
            fontWeight={600}
            color={`${gaugeColor}.main`}
            sx={{ mt: 1 }}
          >
            {readiness.label}
          </Typography>
        </Box>

        {/* Component breakdown */}
        <Stack spacing={1.5} sx={{ mt: 2 }}>
          {components.map((c) => (
            <Box key={c.label}>
              <Stack
                direction="row"
                justifyContent="space-between"
                sx={{ mb: 0.5 }}
              >
                <Typography variant="caption" fontWeight={500}>
                  {c.label}
                  <Typography
                    component="span"
                    variant="caption"
                    color="text.secondary"
                  >
                    {" "}
                    ({c.weight})
                  </Typography>
                </Typography>
                <Typography variant="caption" fontWeight={600}>
                  {c.value}%
                </Typography>
              </Stack>
              <LinearProgress
                variant="determinate"
                value={c.value}
                sx={{ height: 6, borderRadius: 3 }}
                color={
                  c.value >= 70
                    ? "success"
                    : c.value >= 50
                    ? "warning"
                    : "error"
                }
              />
            </Box>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Competency Radar Chart
// ---------------------------------------------------------------------------

function CompetencyRadar({
  dimensions,
}: {
  dimensions: DimensionAverage[];
}) {
  const radarData = dimensions.map((d) => ({
    dimension: d.dimension,
    score: d.average,
    fullMark: 5,
  }));

  // Recharts v3 Polar* components have a ReactNode return type that clashes
  // with React 19's stricter JSX element types. Cast to any to fix.
  const AngleAxis = PolarAngleAxis as any;
  const RadiusAxis = PolarRadiusAxis as any;

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
        <PolarGrid stroke="#e2e8f0" />
        <AngleAxis
          dataKey="dimension"
          tick={{ fontSize: 12, fill: "#4a5568" }}
        />
        <RadiusAxis
          angle={90}
          domain={[0, 5]}
          tick={{ fontSize: 10 }}
          tickCount={6}
        />
        <Tooltip
          formatter={(value: any) => [Number(value).toFixed(1), "Avg Score"]}
        />
        <Radar
          name="Your Scores"
          dataKey="score"
          stroke="#1a365d"
          fill="#1a365d"
          fillOpacity={0.25}
          strokeWidth={2}
          dot={{ r: 4, fill: "#1a365d" }}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}

// ---------------------------------------------------------------------------
// Dimension Breakdown Bars
// ---------------------------------------------------------------------------

function DimensionBars({
  dimensions,
}: {
  dimensions: DimensionAverage[];
}) {
  const barData = dimensions.map((d) => ({
    dimension: d.dimension,
    average: d.average,
    fill: DIMENSION_COLORS[d.dimension] || "#1a365d",
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart
        data={barData}
        layout="vertical"
        margin={{ top: 5, right: 30, left: 60, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" opacity={0.3} horizontal={false} />
        <XAxis type="number" domain={[0, 5]} tick={{ fontSize: 12 }} />
        <YAxis
          type="category"
          dataKey="dimension"
          tick={{ fontSize: 12 }}
          width={80}
        />
        <Tooltip formatter={(value: any) => [Number(value).toFixed(1), "Avg"]} />
        <Bar
          dataKey="average"
          radius={[0, 4, 4, 0]}
          barSize={24}
          label={{
            position: "right",
            fontSize: 12,
            fontWeight: 600,
            formatter: (value: any) => Number(value).toFixed(1),
          }}
        >
          {barData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ---------------------------------------------------------------------------
// Per-Company Table
// ---------------------------------------------------------------------------

function scoreColor(score: number | null): string {
  if (score === null) return "text.secondary";
  if (score >= 4) return "success.main";
  if (score >= 3) return "warning.main";
  return "error.main";
}

function CompanyTable({
  breakdowns,
}: {
  breakdowns: CompanyBreakdown[];
}) {
  return (
    <TableContainer>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell sx={{ fontWeight: 600 }}>Company</TableCell>
            <TableCell align="center" sx={{ fontWeight: 600 }}>
              Evals
            </TableCell>
            <TableCell align="center" sx={{ fontWeight: 600 }}>
              Avg
            </TableCell>
            <TableCell align="center" sx={{ fontWeight: 600 }}>
              Best
            </TableCell>
            <TableCell align="center" sx={{ fontWeight: 600 }}>
              S
            </TableCell>
            <TableCell align="center" sx={{ fontWeight: 600 }}>
              T
            </TableCell>
            <TableCell align="center" sx={{ fontWeight: 600 }}>
              A
            </TableCell>
            <TableCell align="center" sx={{ fontWeight: 600 }}>
              R
            </TableCell>
            <TableCell align="center" sx={{ fontWeight: 600 }}>
              E
            </TableCell>
            <TableCell align="center" sx={{ fontWeight: 600 }}>
              O
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {breakdowns.map((b) => (
            <TableRow key={b.company_name} hover>
              <TableCell>
                <Typography variant="body2" fontWeight={500}>
                  {b.company_name}
                </Typography>
              </TableCell>
              <TableCell align="center">
                <Chip
                  label={b.evaluation_count}
                  size="small"
                  variant="outlined"
                  sx={{ height: 22, fontSize: 11 }}
                />
              </TableCell>
              <TableCell align="center">
                <Typography
                  variant="body2"
                  fontWeight={600}
                  color={scoreColor(b.average_score)}
                >
                  {b.average_score?.toFixed(1) ?? "—"}
                </Typography>
              </TableCell>
              <TableCell align="center">
                <Typography
                  variant="body2"
                  fontWeight={600}
                  color={scoreColor(b.best_score)}
                >
                  {b.best_score?.toFixed(1) ?? "—"}
                </Typography>
              </TableCell>
              {[
                b.situation_avg,
                b.task_avg,
                b.action_avg,
                b.result_avg,
                b.engagement_avg,
                b.overall_avg,
              ].map((score, i) => (
                <TableCell key={i} align="center">
                  <Typography
                    variant="body2"
                    color={scoreColor(score)}
                  >
                    {score?.toFixed(1) ?? "—"}
                  </Typography>
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
