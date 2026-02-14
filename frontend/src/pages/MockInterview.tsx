/**
 * Mock Interview page — timed practice under pressure.
 *
 * Flow:
 * 1. Setup: pick company, role, level, time limit
 * 2. Random question loads → timer starts
 * 3. User writes answer while countdown runs
 * 4. On submit or time expiry → answer is saved + evaluated
 * 5. Navigate to evaluation results
 *
 * The timer runs entirely on the frontend. The backend only tracks
 * the session metadata (time_limit, time_used, completed).
 */

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  FormControl,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import TimerIcon from "@mui/icons-material/Timer";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import SendIcon from "@mui/icons-material/Send";

import {
  listCompanies,
  getRandomQuestion,
  startMockSession,
  completeMockSession,
  createAnswer,
  getAnswer,
  createEvaluation,
  Question,
} from "../api/client";
import UpgradePrompt, { isTierLimitError } from "../components/UpgradePrompt";

const ROLES = ["MLE", "PM", "TPM", "EM"];
const LEVELS = [
  { value: "entry", label: "Entry Level (L3/L4)" },
  { value: "mid", label: "Mid Level (L4/L5)" },
  { value: "senior", label: "Senior (L5/L6)" },
  { value: "staff", label: "Staff+ (L6/L7)" },
];
const TIME_OPTIONS = [
  { value: 120, label: "2 minutes" },
  { value: 180, label: "3 minutes (recommended)" },
  { value: 300, label: "5 minutes" },
  { value: 600, label: "10 minutes" },
];

type Phase = "setup" | "active" | "submitting";

export default function MockInterview() {
  const navigate = useNavigate();
  const location = useLocation();
  const passedQuestionId = (location.state as any)?.questionId || "";
  const passedQuestionText = (location.state as any)?.questionText || "";

  // Setup state
  const [companyId, setCompanyId] = useState("");
  const [role, setRole] = useState("");
  const [level, setLevel] = useState("");
  const [timeLimit, setTimeLimit] = useState(300);

  // Active interview state
  const [phase, setPhase] = useState<Phase>("setup");
  const [question, setQuestion] = useState<Question | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [answerText, setAnswerText] = useState("");
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [error, setError] = useState("");
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [tierLimitInfo, setTierLimitInfo] = useState<{
    currentUsage?: number;
    limit?: number;
  }>({});

  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(0);

  const { data: companies } = useQuery({
    queryKey: ["companies"],
    queryFn: listCompanies,
  });

  const selectedCompany = companies?.find((c) => c.id === companyId);

  // Timer logic
  useEffect(() => {
    if (phase !== "active") return;

    timerRef.current = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          // Time's up — auto-submit
          if (timerRef.current) clearInterval(timerRef.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [phase]);

  const handleStart = async () => {
    setError("");
    try {
      // Use the passed question if available, otherwise get a random one
      let q: Question;
      if (passedQuestionId) {
        q = {
          id: passedQuestionId,
          question_text: passedQuestionText,
          role_tags: [],
          company_tags: [],
          competency_tags: [],
          difficulty: "",
          level_band: null,
          usage_count: 0,
        };
      } else {
        q = await getRandomQuestion({
          role: role || undefined,
          level: level || undefined,
        });
      }
      setQuestion(q);

      // Create mock session on the backend
      const session = await startMockSession({
        question_id: q.id,
        time_limit_seconds: timeLimit,
      });
      setSessionId(session.id);

      // Start the clock
      setSecondsLeft(timeLimit);
      startTimeRef.current = Date.now();
      setPhase("active");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to start mock interview");
    }
  };

  const handleSubmit = useCallback(async () => {
    if (phase === "submitting" || !sessionId || !question) return;
    setPhase("submitting");

    const timeUsed = Math.round((Date.now() - startTimeRef.current) / 1000);

    try {
      // Save the answer (POST returns metadata only, no versions)
      const created = await createAnswer({
        question_id: question.id,
        target_company_id: companyId,
        target_role: role,
        experience_level: level,
        answer_text: answerText,
      });

      // Fetch the full answer with versions to get the version ID
      const answer = await getAnswer(created.id);
      const versionId =
        answer.versions && answer.versions.length > 0
          ? answer.versions[0].id
          : null;

      if (!versionId) {
        setError("Failed to retrieve answer version. Please try again.");
        setPhase("active");
        return;
      }

      // Kick off evaluation
      const evaluation = await createEvaluation(versionId);

      // Complete the mock session
      await completeMockSession(sessionId, {
        time_used_seconds: timeUsed,
        answer_version_id: versionId,
        evaluation_id: evaluation.id,
      });

      // Navigate to results
      navigate(`/evaluations/${evaluation.id}`);
    } catch (err: any) {
      const tierCheck = isTierLimitError(err);
      if (tierCheck.isLimit) {
        setTierLimitInfo({
          currentUsage: tierCheck.currentUsage,
          limit: tierCheck.limit,
        });
        setShowUpgrade(true);
        return;
      }
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : detail?.message || "Failed to submit answer"
      );
      setPhase("active");
    }
  }, [phase, sessionId, question, answerText, companyId, role, level, navigate]);

  // Auto-submit when timer hits 0
  useEffect(() => {
    if (phase === "active" && secondsLeft === 0 && answerText.trim().length > 0) {
      handleSubmit();
    }
  }, [secondsLeft, phase, answerText, handleSubmit]);

  // Format seconds as MM:SS
  const formatTime = (s: number) => {
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // Timer color based on urgency
  const timerColor =
    secondsLeft <= 30 ? "error" : secondsLeft <= 60 ? "warning" : "primary";

  const timerPct = timeLimit > 0 ? (secondsLeft / timeLimit) * 100 : 0;

  const wordCount = answerText.trim().split(/\s+/).filter(Boolean).length;

  // ----- Setup phase -----
  if (phase === "setup") {
    return (
      <Box sx={{ maxWidth: 600, mx: "auto" }}>
        <Typography variant="h4" gutterBottom>
          <TimerIcon sx={{ mr: 1, verticalAlign: "bottom" }} />
          Mock Interview
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          Practice answering under time pressure.{" "}
          {passedQuestionText
            ? "Your selected question is ready below."
            : "You'll get a random question."}{" "}
          When time runs out, your answer is submitted automatically.
        </Typography>

        {passedQuestionText && (
          <Alert severity="info" sx={{ mb: 2 }}>
            <strong>Selected Question:</strong> {passedQuestionText}
          </Alert>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Card>
          <CardContent>
            <Stack spacing={3}>
              {/* Company */}
              <FormControl fullWidth>
                <InputLabel>Target Company</InputLabel>
                <Select
                  value={companyId}
                  label="Target Company"
                  onChange={(e) => setCompanyId(e.target.value)}
                >
                  {companies?.map((c) => (
                    <MenuItem key={c.id} value={c.id}>
                      {c.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Role */}
              <FormControl fullWidth>
                <InputLabel>Target Role</InputLabel>
                <Select
                  value={role}
                  label="Target Role"
                  onChange={(e) => setRole(e.target.value)}
                >
                  {ROLES.map((r) => (
                    <MenuItem key={r} value={r}>
                      {r}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Level */}
              <FormControl fullWidth>
                <InputLabel>Experience Level</InputLabel>
                <Select
                  value={level}
                  label="Experience Level"
                  onChange={(e) => setLevel(e.target.value)}
                >
                  {LEVELS.map((l) => (
                    <MenuItem key={l.value} value={l.value}>
                      {l.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Time Limit */}
              <FormControl fullWidth>
                <InputLabel>Time Limit</InputLabel>
                <Select
                  value={timeLimit}
                  label="Time Limit"
                  onChange={(e) => setTimeLimit(Number(e.target.value))}
                >
                  {TIME_OPTIONS.map((t) => (
                    <MenuItem key={t.value} value={t.value}>
                      {t.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Button
                variant="contained"
                size="large"
                startIcon={<PlayArrowIcon />}
                onClick={handleStart}
                disabled={!companyId || !role || !level}
              >
                Start Mock Interview
              </Button>
            </Stack>
          </CardContent>
        </Card>
      </Box>
    );
  }

  // ----- Active / Submitting phase -----
  return (
    <Box sx={{ maxWidth: 800, mx: "auto" }}>
      {/* Timer bar */}
      <Card sx={{ mb: 2, bgcolor: secondsLeft <= 30 ? "error.light" : undefined }}>
        <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1 }}>
            <TimerIcon color={timerColor as any} />
            <Typography
              variant="h4"
              fontWeight={700}
              color={`${timerColor}.main`}
              sx={{ fontFamily: "monospace" }}
            >
              {formatTime(secondsLeft)}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ ml: "auto" }}>
              {selectedCompany?.name} &middot; {role} &middot; {level}
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={timerPct}
            color={timerColor as any}
          />
        </CardContent>
      </Card>

      {/* Question */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="overline" color="text.secondary">
            Your Question
          </Typography>
          <Typography variant="h6">{question?.question_text}</Typography>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Answer area */}
      <TextField
        fullWidth
        multiline
        minRows={10}
        maxRows={20}
        placeholder="Start typing your STAR answer... (Situation → Task → Action → Result)"
        value={answerText}
        onChange={(e) => setAnswerText(e.target.value)}
        disabled={phase === "submitting"}
        autoFocus
        sx={{ mb: 2 }}
      />

      <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
        <Typography variant="body2" color="text.secondary">
          {wordCount} words
        </Typography>
        <Box sx={{ flexGrow: 1 }} />
        <Button
          variant="contained"
          endIcon={
            phase === "submitting" ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              <SendIcon />
            )
          }
          onClick={handleSubmit}
          disabled={phase === "submitting" || answerText.trim().length < 10}
        >
          {phase === "submitting" ? "Submitting..." : "Submit & Evaluate"}
        </Button>
      </Box>

      {/* Upgrade prompt when tier limit is reached */}
      <UpgradePrompt
        open={showUpgrade}
        onClose={() => setShowUpgrade(false)}
        currentUsage={tierLimitInfo.currentUsage}
        limit={tierLimitInfo.limit}
      />
    </Box>
  );
}
