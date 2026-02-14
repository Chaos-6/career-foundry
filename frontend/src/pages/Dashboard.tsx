/**
 * Dashboard page — personalized landing hub.
 *
 * Shows different content based on auth state:
 *
 * Unauthenticated:
 * - 4 feature cards (Evaluate, Mock, Generator, Question Bank)
 * - "How It Works" explainer
 *
 * Authenticated:
 * - Stats summary bar (total evals, avg score, best score)
 * - Score trend chart (Recharts area chart)
 * - Recent evaluations table with quick-links
 * - Feature cards (collapsed to 1 row)
 */

import React from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  Paper,
  Skeleton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import RateReviewIcon from "@mui/icons-material/RateReview";
import QuizIcon from "@mui/icons-material/Quiz";
import TimerIcon from "@mui/icons-material/Timer";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import AssessmentIcon from "@mui/icons-material/Assessment";
import EmojiEventsIcon from "@mui/icons-material/EmojiEvents";
import LocalFireDepartmentIcon from "@mui/icons-material/LocalFireDepartment";
import ExploreIcon from "@mui/icons-material/Explore";
import StarIcon from "@mui/icons-material/Star";
import HistoryIcon from "@mui/icons-material/History";
import LockIcon from "@mui/icons-material/Lock";
import LockOpenIcon from "@mui/icons-material/LockOpen";
import ReplayIcon from "@mui/icons-material/Replay";
import SchoolIcon from "@mui/icons-material/School";
import VisibilityIcon from "@mui/icons-material/Visibility";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

import { useAuth } from "../hooks/useAuth";
import {
  getDashboardStats,
  getRecentEvaluations,
  getScoreHistory,
  getRecommendedQuestions,
  DashboardStats,
  BadgeInfo,
  StreakInfo,
  RecentEvaluation,
  RecommendedQuestion,
  ScoreDataPoint,
} from "../api/client";

// ---------------------------------------------------------------------------
// Static data
// ---------------------------------------------------------------------------

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

// Chart colors per dimension
const CHART_COLORS: Record<string, string> = {
  average: "#1a365d",   // navy — primary theme color
  situation: "#38a169", // green
  task: "#3182ce",      // blue
  action: "#d69e2e",    // amber
  result: "#805ad5",    // purple
  engagement: "#e53e3e", // red
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function Dashboard() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  return (
    <Box sx={{ maxWidth: 960, mx: "auto" }}>
      {/* Hero */}
      <Box sx={{ mb: 3 }}>
        <Typography
          variant="h4"
          gutterBottom
          fontWeight={700}
          sx={{ fontSize: { xs: "1.5rem", sm: "2.125rem" } }}
        >
          Welcome to BIAE
        </Typography>
        <Typography
          variant="h6"
          color="text.secondary"
          fontWeight={400}
          sx={{ fontSize: { xs: "0.95rem", sm: "1.25rem" } }}
        >
          AI-powered STAR answer coaching for tech interview preparation
        </Typography>
      </Box>

      {/* Authenticated users see personalized dashboard */}
      {isAuthenticated && <AuthenticatedDashboard />}

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

      {/* How It Works — only for unauthenticated users (they already know) */}
      {!isAuthenticated && (
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
      )}
    </Box>
  );
}

// ---------------------------------------------------------------------------
// Authenticated Dashboard — stats, chart, recent evaluations
// ---------------------------------------------------------------------------

function AuthenticatedDashboard() {
  const {
    data: stats,
    isLoading: statsLoading,
  } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: getDashboardStats,
    staleTime: 60_000,
  });

  const {
    data: recent,
    isLoading: recentLoading,
  } = useQuery({
    queryKey: ["dashboard-recent"],
    queryFn: () => getRecentEvaluations(8),
    staleTime: 60_000,
  });

  const {
    data: scoreHistory,
    isLoading: historyLoading,
  } = useQuery({
    queryKey: ["dashboard-score-history"],
    queryFn: () => getScoreHistory(30),
    staleTime: 60_000,
  });

  const {
    data: recommended,
  } = useQuery({
    queryKey: ["dashboard-recommended"],
    queryFn: () => getRecommendedQuestions(5),
    staleTime: 60_000,
  });

  return (
    <>
      {/* Stats Summary */}
      <StatsBar stats={stats ?? null} loading={statsLoading} />

      {/* Streak & Badges */}
      {!statsLoading && stats && (
        <StreakAndBadges streak={stats.streak} badges={stats.badges} />
      )}

      {/* Recommended for You (Spaced Repetition) */}
      {recommended && recommended.length > 0 && (
        <RecommendedForYou questions={recommended} />
      )}

      {/* Score Trend Chart */}
      {(historyLoading || (scoreHistory && scoreHistory.length > 1)) && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom fontWeight={600}>
              <TrendingUpIcon
                sx={{ mr: 1, verticalAlign: "middle", fontSize: 22 }}
              />
              Score Trend
            </Typography>
            {historyLoading ? (
              <Skeleton variant="rectangular" height={260} />
            ) : (
              <ScoreTrendChart data={scoreHistory!} />
            )}
          </CardContent>
        </Card>
      )}

      {/* Recent Evaluations */}
      {(recentLoading || (recent && recent.length > 0)) && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom fontWeight={600}>
              <HistoryIcon
                sx={{ mr: 1, verticalAlign: "middle", fontSize: 22 }}
              />
              Recent Evaluations
            </Typography>
            {recentLoading ? (
              <Stack spacing={1}>
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} variant="rectangular" height={40} />
                ))}
              </Stack>
            ) : (
              <RecentEvaluationsTable evaluations={recent!} />
            )}
          </CardContent>
        </Card>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Stats Bar
// ---------------------------------------------------------------------------

function StatsBar({
  stats,
  loading,
}: {
  stats: DashboardStats | null;
  loading: boolean;
}) {
  const statCards = [
    {
      icon: <AssessmentIcon sx={{ fontSize: 28, color: "primary.main" }} />,
      label: "Total Evaluations",
      value: stats?.total_evaluations ?? 0,
    },
    {
      icon: <TrendingUpIcon sx={{ fontSize: 28, color: "secondary.main" }} />,
      label: "Average Score",
      value: stats?.average_score != null ? `${stats.average_score}/5` : "—",
    },
    {
      icon: <EmojiEventsIcon sx={{ fontSize: 28, color: "warning.main" }} />,
      label: "Best Score",
      value: stats?.best_score != null ? `${stats.best_score}/5` : "—",
    },
    {
      icon: <HistoryIcon sx={{ fontSize: 28, color: "info.main" }} />,
      label: "This Month",
      value: stats?.evaluations_this_month ?? 0,
    },
  ];

  return (
    <Grid container spacing={2} sx={{ mb: 3 }}>
      {statCards.map((s) => (
        <Grid item xs={6} sm={3} key={s.label}>
          <Paper
            elevation={0}
            sx={{
              p: 2,
              textAlign: "center",
              border: 1,
              borderColor: "divider",
              borderRadius: 2,
            }}
          >
            {loading ? (
              <Skeleton variant="rectangular" height={60} />
            ) : (
              <>
                <Box sx={{ mb: 0.5 }}>{s.icon}</Box>
                <Typography variant="h5" fontWeight={700}>
                  {s.value}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {s.label}
                </Typography>
              </>
            )}
          </Paper>
        </Grid>
      ))}
    </Grid>
  );
}

// ---------------------------------------------------------------------------
// Score Trend Chart
// ---------------------------------------------------------------------------

function ScoreTrendChart({ data }: { data: ScoreDataPoint[] }) {
  // Format dates for the x-axis
  const chartData = data.map((d) => ({
    ...d,
    label: new Date(d.date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
        <XAxis dataKey="label" tick={{ fontSize: 12 }} />
        <YAxis domain={[0, 5]} tick={{ fontSize: 12 }} />
        <Tooltip
          contentStyle={{ fontSize: 13 }}
          labelFormatter={(label) => `Date: ${label}`}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Area
          type="monotone"
          dataKey="average"
          name="Average"
          stroke={CHART_COLORS.average}
          fill={CHART_COLORS.average}
          fillOpacity={0.15}
          strokeWidth={2.5}
          dot={{ r: 3 }}
        />
        <Area
          type="monotone"
          dataKey="situation"
          name="Situation"
          stroke={CHART_COLORS.situation}
          fill={CHART_COLORS.situation}
          fillOpacity={0.05}
          strokeWidth={1.5}
          dot={false}
        />
        <Area
          type="monotone"
          dataKey="action"
          name="Action"
          stroke={CHART_COLORS.action}
          fill={CHART_COLORS.action}
          fillOpacity={0.05}
          strokeWidth={1.5}
          dot={false}
        />
        <Area
          type="monotone"
          dataKey="result"
          name="Result"
          stroke={CHART_COLORS.result}
          fill={CHART_COLORS.result}
          fillOpacity={0.05}
          strokeWidth={1.5}
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

// ---------------------------------------------------------------------------
// Recent Evaluations Table
// ---------------------------------------------------------------------------

function scoreColor(score: number | null): string {
  if (score === null) return "text.secondary";
  if (score >= 4) return "success.main";
  if (score >= 3) return "warning.main";
  return "error.main";
}

function RecentEvaluationsTable({
  evaluations,
}: {
  evaluations: RecentEvaluation[];
}) {
  const navigate = useNavigate();

  const hiddenOnMobile = { display: { xs: "none", sm: "table-cell" } };

  return (
    <TableContainer sx={{ overflowX: "auto" }}>
      <Table size="small" sx={{ minWidth: { xs: 400, sm: "auto" } }}>
        <TableHead>
          <TableRow>
            <TableCell sx={{ fontWeight: 600 }}>Question</TableCell>
            <TableCell sx={{ fontWeight: 600, ...hiddenOnMobile }}>Company</TableCell>
            <TableCell sx={{ fontWeight: 600, ...hiddenOnMobile }}>Role</TableCell>
            <TableCell align="center" sx={{ fontWeight: 600 }}>
              Score
            </TableCell>
            <TableCell align="center" sx={{ fontWeight: 600, ...hiddenOnMobile }}>
              Status
            </TableCell>
            <TableCell sx={{ fontWeight: 600, ...hiddenOnMobile }}>Date</TableCell>
            <TableCell />
          </TableRow>
        </TableHead>
        <TableBody>
          {evaluations.map((ev) => (
            <TableRow
              key={ev.evaluation_id}
              hover
              sx={{ cursor: "pointer" }}
              onClick={() => navigate(`/evaluations/${ev.evaluation_id}`)}
            >
              <TableCell sx={{ maxWidth: { xs: 160, sm: 240 } }}>
                <Typography variant="body2" noWrap>
                  {ev.question_text || "Custom question"}
                </Typography>
              </TableCell>
              <TableCell sx={hiddenOnMobile}>
                <Typography variant="body2">{ev.company_name}</Typography>
              </TableCell>
              <TableCell sx={hiddenOnMobile}>
                <Typography variant="body2">{ev.target_role}</Typography>
              </TableCell>
              <TableCell align="center">
                {ev.average_score != null ? (
                  <Typography
                    variant="body2"
                    fontWeight={600}
                    color={scoreColor(ev.average_score)}
                  >
                    {ev.average_score}
                  </Typography>
                ) : (
                  "—"
                )}
              </TableCell>
              <TableCell align="center" sx={hiddenOnMobile}>
                <Chip
                  label={ev.status}
                  size="small"
                  color={
                    ev.status === "completed"
                      ? "success"
                      : ev.status === "failed"
                      ? "error"
                      : "primary"
                  }
                  variant="outlined"
                  sx={{ height: 22, fontSize: 11 }}
                />
              </TableCell>
              <TableCell sx={hiddenOnMobile}>
                <Typography variant="caption" color="text.secondary">
                  {new Date(ev.created_at).toLocaleDateString()}
                </Typography>
              </TableCell>
              <TableCell>
                <Button
                  size="small"
                  startIcon={<VisibilityIcon />}
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/evaluations/${ev.evaluation_id}`);
                  }}
                >
                  View
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

// ---------------------------------------------------------------------------
// Streak & Badges Widget
// ---------------------------------------------------------------------------

const BADGE_ICONS: Record<string, React.ReactNode> = {
  emoji_events: <EmojiEventsIcon />,
  local_fire_department: <LocalFireDepartmentIcon />,
  star: <StarIcon />,
  explore: <ExploreIcon />,
  trending_up: <TrendingUpIcon />,
  timer: <TimerIcon />,
};

function StreakAndBadges({
  streak,
  badges,
}: {
  streak: StreakInfo | null;
  badges: BadgeInfo[];
}) {
  const unlockedCount = badges.filter((b) => b.unlocked).length;

  return (
    <Grid container spacing={3} sx={{ mb: 3 }}>
      {/* Streak Card */}
      <Grid item xs={12} sm={4}>
        <Card sx={{ height: "100%" }}>
          <CardContent sx={{ textAlign: "center", py: 3 }}>
            <LocalFireDepartmentIcon
              sx={{
                fontSize: 48,
                color: streak?.streak_active ? "warning.main" : "action.disabled",
                mb: 1,
              }}
            />
            <Typography variant="h3" fontWeight={700} color={streak?.streak_active ? "warning.main" : "text.secondary"}>
              {streak?.current_streak ?? 0}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Day Streak
            </Typography>
            <Chip
              label={`Best: ${streak?.longest_streak ?? 0} days`}
              size="small"
              variant="outlined"
            />
            {streak && !streak.streak_active && streak.current_streak > 0 && (
              <Typography variant="caption" display="block" color="error" sx={{ mt: 1 }}>
                Practice today to keep your streak!
              </Typography>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Badges Card */}
      <Grid item xs={12} sm={8}>
        <Card sx={{ height: "100%" }}>
          <CardContent>
            <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
              <EmojiEventsIcon sx={{ color: "warning.main", fontSize: 22 }} />
              <Typography variant="h6" fontWeight={600}>
                Achievements
              </Typography>
              <Chip
                label={`${unlockedCount}/${badges.length}`}
                size="small"
                color={unlockedCount === badges.length ? "success" : "default"}
              />
            </Stack>
            <Grid container spacing={1.5}>
              {badges.map((badge) => (
                <Grid item xs={6} sm={4} key={badge.id}>
                  <Paper
                    elevation={0}
                    sx={{
                      p: 1.5,
                      textAlign: "center",
                      border: 1,
                      borderColor: badge.unlocked ? "warning.main" : "divider",
                      borderRadius: 2,
                      bgcolor: badge.unlocked ? "warning.50" : "action.hover",
                      opacity: badge.unlocked ? 1 : 0.6,
                      transition: "all 0.2s",
                    }}
                  >
                    <Box
                      sx={{
                        color: badge.unlocked ? "warning.main" : "action.disabled",
                        mb: 0.5,
                      }}
                    >
                      {badge.unlocked
                        ? (BADGE_ICONS[badge.icon] || <EmojiEventsIcon />)
                        : <LockIcon />}
                    </Box>
                    <Typography
                      variant="caption"
                      fontWeight={600}
                      display="block"
                      noWrap
                    >
                      {badge.name}
                    </Typography>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      display="block"
                      sx={{ fontSize: 10, lineHeight: 1.2, mt: 0.25 }}
                    >
                      {badge.description}
                    </Typography>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}

// ---------------------------------------------------------------------------
// Recommended for You (Spaced Repetition)
// ---------------------------------------------------------------------------

function RecommendedForYou({
  questions,
}: {
  questions: RecommendedQuestion[];
}) {
  const navigate = useNavigate();

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          <SchoolIcon
            sx={{ mr: 1, verticalAlign: "middle", fontSize: 22 }}
          />
          Recommended for You
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Questions where you scored ≤ 3.5, ordered by how long ago you
          practiced. Focus on these to strengthen weak areas.
        </Typography>
        <Stack spacing={1.5}>
          {questions.map((q) => (
            <Paper
              key={q.answer_id}
              elevation={0}
              sx={{
                p: 2,
                border: 1,
                borderColor: "divider",
                borderRadius: 2,
                "&:hover": { borderColor: "primary.main", bgcolor: "action.hover" },
                transition: "all 0.15s",
              }}
            >
              <Stack
                direction={{ xs: "column", sm: "row" }}
                justifyContent="space-between"
                alignItems={{ xs: "flex-start", sm: "center" }}
                spacing={1}
              >
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="body2" fontWeight={500} noWrap>
                    {q.question_text}
                  </Typography>
                  <Stack direction="row" spacing={1} sx={{ mt: 0.5 }}>
                    <Chip label={q.company_name} size="small" variant="outlined" />
                    <Chip label={q.target_role} size="small" variant="outlined" />
                    <Typography
                      variant="caption"
                      color={q.best_score <= 2.5 ? "error.main" : "warning.main"}
                      fontWeight={600}
                    >
                      Score: {q.best_score}/5
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      · {q.days_since_practice}d ago
                    </Typography>
                  </Stack>
                </Box>
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<ReplayIcon />}
                  onClick={() =>
                    navigate("/evaluate", {
                      state: { questionId: q.question_id },
                    })
                  }
                  sx={{ flexShrink: 0 }}
                >
                  Practice Again
                </Button>
              </Stack>
            </Paper>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}
