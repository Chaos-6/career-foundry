/**
 * Dashboard page — the product's front door.
 *
 * Unauthenticated:
 * - Hero with value proposition
 * - Feature cards (evaluate, mock, generator, question bank)
 * - "How It Works" steps
 * - Social proof markers
 *
 * Authenticated:
 * - Stats summary bar
 * - Score trend chart
 * - Recent evaluations table
 * - Streak & badges
 * - Recommended practice questions
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
import ReplayIcon from "@mui/icons-material/Replay";
import SchoolIcon from "@mui/icons-material/School";
import VisibilityIcon from "@mui/icons-material/Visibility";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import SmartToyIcon from "@mui/icons-material/SmartToy";
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
    label: "STAR Evaluation",
    icon: <RateReviewIcon sx={{ fontSize: 32 }} />,
    desc: "Get your behavioral answer scored across 6 dimensions with company-specific alignment.",
    color: "#1a365d",
    bgLight: "#eef2f7",
  },
  {
    path: "/mock",
    label: "Mock Interview",
    icon: <TimerIcon sx={{ fontSize: 32 }} />,
    desc: "Practice under realistic time pressure with random questions and auto-scoring.",
    color: "#e53e3e",
    bgLight: "#fff5f5",
  },
  {
    path: "/generator",
    label: "AI Generator",
    icon: <AutoAwesomeIcon sx={{ fontSize: 32 }} />,
    desc: "Enter bullet points. Get a polished STAR narrative draft you can refine and evaluate.",
    color: "#38a169",
    bgLight: "#f0fff4",
  },
  {
    path: "/questions",
    label: "Question Bank",
    icon: <QuizIcon sx={{ fontSize: 32 }} />,
    desc: "80+ curated behavioral questions filtered by role, company, and competency.",
    color: "#3182ce",
    bgLight: "#ebf8ff",
  },
];

const steps = [
  {
    num: "01",
    title: "Set the Context",
    desc: "Select your target company, role, and level. We load their leadership principles to tailor feedback.",
  },
  {
    num: "02",
    title: "Pick a Question",
    desc: "Choose from the curated bank or paste your own behavioral question.",
  },
  {
    num: "03",
    title: "Write Your Answer",
    desc: "Draft your STAR-formatted answer. Use voice dictation to practice delivery.",
  },
  {
    num: "04",
    title: "Get AI Feedback",
    desc: "Claude scores 6 dimensions, highlights strengths, and shows exactly what a Staff Engineer would say.",
  },
  {
    num: "05",
    title: "Revise & Improve",
    desc: "Edit your answer, re-evaluate, and track score improvements version over version.",
  },
];

const CHART_COLORS: Record<string, string> = {
  average: "#1a365d",
  situation: "#38a169",
  task: "#3182ce",
  action: "#d69e2e",
  result: "#805ad5",
  engagement: "#e53e3e",
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function Dashboard() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  return (
    <Box sx={{ maxWidth: 960, mx: "auto" }}>
      {/* Hero Section */}
      <Box
        sx={{
          mb: 4,
          py: { xs: 3, sm: 5 },
          px: { xs: 2, sm: 4 },
          borderRadius: 3,
          background: "linear-gradient(135deg, #1a365d 0%, #2b6cb0 100%)",
          color: "white",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Decorative background element */}
        <Box
          sx={{
            position: "absolute",
            top: -40,
            right: -40,
            width: 200,
            height: 200,
            borderRadius: "50%",
            bgcolor: "rgba(255,255,255,0.06)",
          }}
        />
        <Box
          sx={{
            position: "absolute",
            bottom: -60,
            right: 80,
            width: 160,
            height: 160,
            borderRadius: "50%",
            bgcolor: "rgba(255,255,255,0.04)",
          }}
        />

        <Box sx={{ position: "relative", zIndex: 1 }}>
          <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1.5 }}>
            <SmartToyIcon sx={{ fontSize: 28 }} />
            <Typography variant="overline" sx={{ fontWeight: 600, letterSpacing: "0.1em", opacity: 0.9 }}>
              Career Foundry
            </Typography>
          </Stack>
          <Typography
            variant="h3"
            fontWeight={800}
            sx={{
              fontSize: { xs: "1.75rem", sm: "2.5rem" },
              lineHeight: 1.2,
              mb: 1.5,
              letterSpacing: "-0.02em",
            }}
          >
            Nail your next behavioral interview
          </Typography>
          <Typography
            variant="h6"
            fontWeight={400}
            sx={{
              opacity: 0.85,
              maxWidth: 560,
              fontSize: { xs: "0.95rem", sm: "1.15rem" },
              lineHeight: 1.5,
              mb: 3,
            }}
          >
            AI-powered STAR answer coaching with scored feedback, company alignment analysis,
            and side-by-side rewrites from a Staff Engineer.
          </Typography>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
            <Button
              variant="contained"
              size="large"
              endIcon={<ArrowForwardIcon />}
              onClick={() => navigate("/evaluate")}
              sx={{
                bgcolor: "white",
                color: "primary.main",
                fontWeight: 700,
                "&:hover": {
                  bgcolor: "rgba(255,255,255,0.9)",
                  transform: "translateY(-1px)",
                },
              }}
            >
              Start Free Evaluation
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate("/questions")}
              sx={{
                borderColor: "rgba(255,255,255,0.4)",
                color: "white",
                "&:hover": {
                  borderColor: "white",
                  bgcolor: "rgba(255,255,255,0.1)",
                },
              }}
            >
              Browse Questions
            </Button>
          </Stack>
        </Box>
      </Box>

      {/* Stats for authenticated users */}
      {isAuthenticated && <AuthenticatedDashboard />}

      {/* Feature cards */}
      <Grid container spacing={2.5} sx={{ mb: 4 }}>
        {features.map((f) => (
          <Grid item xs={12} sm={6} key={f.path}>
            <Card
              sx={{
                height: "100%",
                cursor: "pointer",
                border: 1,
                borderColor: "transparent",
                "&:hover": {
                  boxShadow: 6,
                  borderColor: f.color,
                  transform: "translateY(-3px)",
                },
                transition: "all 0.2s ease",
              }}
              onClick={() => navigate(f.path)}
            >
              <CardContent sx={{ p: 3 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: "12px",
                    bgcolor: f.bgLight,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: f.color,
                    mb: 2,
                  }}
                >
                  {f.icon}
                </Box>
                <Typography variant="h6" gutterBottom sx={{ fontSize: "1.05rem" }}>
                  {f.label}
                </Typography>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ lineHeight: 1.6 }}
                >
                  {f.desc}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* How It Works — only for unauthenticated users */}
      {!isAuthenticated && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" fontWeight={700} sx={{ mb: 3 }}>
            How it works
          </Typography>
          <Grid container spacing={2}>
            {steps.map((s) => (
              <Grid item xs={12} sm={6} md={4} key={s.num}>
                <Box sx={{ display: "flex", gap: 2, alignItems: "flex-start" }}>
                  <Typography
                    variant="h4"
                    sx={{
                      fontWeight: 800,
                      color: "primary.light",
                      opacity: 0.25,
                      lineHeight: 1,
                      flexShrink: 0,
                      userSelect: "none",
                    }}
                  >
                    {s.num}
                  </Typography>
                  <Box>
                    <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                      {s.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                      {s.desc}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Credibility markers — unauthenticated only */}
      {!isAuthenticated && (
        <Box sx={{ mb: 3 }}>
          <Stack
            direction="row"
            spacing={3}
            justifyContent="center"
            flexWrap="wrap"
            sx={{
              py: 3,
              px: 2,
              bgcolor: "background.paper",
              borderRadius: 2,
              border: 1,
              borderColor: "divider",
            }}
          >
            {[
              { label: "22+ companies", sub: "with researched principles" },
              { label: "80+ questions", sub: "curated question bank" },
              { label: "6 dimensions", sub: "scored per answer" },
              { label: "Claude AI", sub: "powered by Anthropic" },
            ].map((stat) => (
              <Box key={stat.label} sx={{ textAlign: "center", minWidth: 120 }}>
                <Typography variant="h6" fontWeight={700} color="primary.main">
                  {stat.label}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {stat.sub}
                </Typography>
              </Box>
            ))}
          </Stack>
        </Box>
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
              <Skeleton variant="rectangular" height={260} sx={{ borderRadius: 2 }} />
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
                  <Skeleton key={i} variant="rectangular" height={40} sx={{ borderRadius: 1 }} />
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
      icon: <AssessmentIcon sx={{ fontSize: 24, color: "primary.main" }} />,
      label: "Total Evaluations",
      value: stats?.total_evaluations ?? 0,
      color: "#eef2f7",
    },
    {
      icon: <TrendingUpIcon sx={{ fontSize: 24, color: "secondary.main" }} />,
      label: "Average Score",
      value: stats?.average_score != null ? `${stats.average_score}/5` : "\u2014",
      color: "#f0fff4",
    },
    {
      icon: <EmojiEventsIcon sx={{ fontSize: 24, color: "warning.main" }} />,
      label: "Best Score",
      value: stats?.best_score != null ? `${stats.best_score}/5` : "\u2014",
      color: "#fffbeb",
    },
    {
      icon: <HistoryIcon sx={{ fontSize: 24, color: "info.main" }} />,
      label: "This Month",
      value: stats?.evaluations_this_month ?? 0,
      color: "#ebf8ff",
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
              borderRadius: 2,
              bgcolor: s.color,
              transition: "transform 0.15s ease",
              "&:hover": { transform: "translateY(-2px)" },
            }}
          >
            {loading ? (
              <Skeleton variant="rectangular" height={60} sx={{ borderRadius: 1 }} />
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
          contentStyle={{ fontSize: 13, borderRadius: 8 }}
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
                  "\u2014"
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
          Questions where you scored &le; 3.5, ordered by how long ago you
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
                      &middot; {q.days_since_practice}d ago
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
