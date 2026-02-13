/**
 * AI Answer Generator page.
 *
 * Flow:
 * 1. Select company, role, level, question
 * 2. Enter bullet points for each STAR component
 * 3. AI generates a polished narrative
 * 4. User reviews and edits the draft
 * 5. Submit edited version for evaluation
 *
 * The bullet-point → narrative step uses a separate Claude call
 * with a different prompt and higher temperature than evaluation.
 */

import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import EditIcon from "@mui/icons-material/Edit";
import SendIcon from "@mui/icons-material/Send";

import {
  listCompanies,
  listQuestions,
  generateAnswer,
  createAnswer,
  getAnswer,
  createEvaluation,
} from "../api/client";

const ROLES = ["MLE", "PM", "TPM", "EM"];
const LEVELS = [
  { value: "entry", label: "Entry Level (L3/L4)" },
  { value: "mid", label: "Mid Level (L4/L5)" },
  { value: "senior", label: "Senior (L5/L6)" },
  { value: "staff", label: "Staff+ (L6/L7)" },
];

type Phase = "input" | "generating" | "editing" | "submitting";

export default function AnswerGenerator() {
  const navigate = useNavigate();
  const location = useLocation();
  const passedQuestionId = (location.state as any)?.questionId || "";

  // Context
  const [companyId, setCompanyId] = useState("");
  const [role, setRole] = useState("");
  const [level, setLevel] = useState("");
  const [questionId, setQuestionId] = useState(passedQuestionId);
  const [customQuestion, setCustomQuestion] = useState("");

  // Bullet inputs
  const [situation, setSituation] = useState("");
  const [task, setTask] = useState("");
  const [action, setAction] = useState("");
  const [result, setResult] = useState("");

  // Generated output
  const [phase, setPhase] = useState<Phase>("input");
  const [generatedText, setGeneratedText] = useState("");
  const [editedText, setEditedText] = useState("");
  const [genStats, setGenStats] = useState<{
    word_count: number;
    processing_seconds: number;
  } | null>(null);
  const [error, setError] = useState("");

  const { data: companies } = useQuery({
    queryKey: ["companies"],
    queryFn: listCompanies,
  });

  const { data: questions } = useQuery({
    queryKey: ["questions", role, level],
    queryFn: () =>
      listQuestions({
        role: role || undefined,
        level: level || undefined,
        limit: 100,
      }),
    enabled: true,
  });

  const selectedCompany = companies?.find((c) => c.id === companyId);
  const selectedQuestion = questions?.items.find((q) => q.id === questionId);
  const questionText =
    selectedQuestion?.question_text || customQuestion || "";

  const canGenerate =
    companyId &&
    role &&
    level &&
    questionText.length >= 10 &&
    situation.trim().length >= 5 &&
    task.trim().length >= 5 &&
    action.trim().length >= 5 &&
    result.trim().length >= 5;

  const handleGenerate = async () => {
    if (!selectedCompany) return;
    setError("");
    setPhase("generating");

    try {
      const res = await generateAnswer({
        question_text: questionText,
        company_name: selectedCompany.name,
        target_role: role,
        experience_level: level,
        situation_bullets: situation,
        task_bullets: task,
        action_bullets: action,
        result_bullets: result,
      });

      setGeneratedText(res.answer_text);
      setEditedText(res.answer_text);
      setGenStats({
        word_count: res.word_count,
        processing_seconds: res.processing_seconds,
      });
      setPhase("editing");
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Failed to generate answer. Please try again."
      );
      setPhase("input");
    }
  };

  const handleSubmitForEvaluation = async () => {
    setError("");
    setPhase("submitting");

    try {
      // POST returns metadata only (no versions), so fetch detail after
      const created = await createAnswer({
        question_id: questionId || undefined,
        custom_question_text: questionId ? undefined : customQuestion,
        target_company_id: companyId,
        target_role: role,
        experience_level: level,
        answer_text: editedText,
        is_ai_assisted: true,
      });

      // Fetch full answer with versions to get the version ID
      const answer = await getAnswer(created.id);
      const versionId =
        answer.versions && answer.versions.length > 0
          ? answer.versions[0].id
          : null;

      if (!versionId) {
        setError("Failed to retrieve answer version. Please try again.");
        setPhase("editing");
        return;
      }

      const evaluation = await createEvaluation(versionId);
      navigate(`/evaluations/${evaluation.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to submit for evaluation");
      setPhase("editing");
    }
  };

  const wordCount = editedText.trim().split(/\s+/).filter(Boolean).length;

  return (
    <Box sx={{ maxWidth: 800, mx: "auto" }}>
      <Typography variant="h4" gutterBottom>
        <AutoAwesomeIcon sx={{ mr: 1, verticalAlign: "bottom" }} />
        AI Answer Generator
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Enter bullet points for each STAR component and let AI craft a polished
        narrative. Review, edit, then submit for evaluation.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* ---- Phase: Input (bullet points) ---- */}
      {(phase === "input" || phase === "generating") && (
        <>
          {/* Context section */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Interview Context
              </Typography>
              <Stack spacing={2}>
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

                <Box sx={{ display: "flex", gap: 2 }}>
                  <FormControl fullWidth>
                    <InputLabel>Role</InputLabel>
                    <Select
                      value={role}
                      label="Role"
                      onChange={(e) => setRole(e.target.value)}
                    >
                      {ROLES.map((r) => (
                        <MenuItem key={r} value={r}>
                          {r}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl fullWidth>
                    <InputLabel>Level</InputLabel>
                    <Select
                      value={level}
                      label="Level"
                      onChange={(e) => setLevel(e.target.value)}
                    >
                      {LEVELS.map((l) => (
                        <MenuItem key={l.value} value={l.value}>
                          {l.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>

                {/* Question selection */}
                <FormControl fullWidth>
                  <InputLabel>Select a Question</InputLabel>
                  <Select
                    value={questionId}
                    label="Select a Question"
                    onChange={(e) => {
                      setQuestionId(e.target.value);
                      setCustomQuestion("");
                    }}
                  >
                    <MenuItem value="">
                      <em>Or type a custom question below</em>
                    </MenuItem>
                    {questions?.items.map((q) => (
                      <MenuItem key={q.id} value={q.id}>
                        {q.question_text}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                {!questionId && (
                  <TextField
                    fullWidth
                    label="Custom Question"
                    placeholder="Tell me about a time you..."
                    value={customQuestion}
                    onChange={(e) => setCustomQuestion(e.target.value)}
                  />
                )}
              </Stack>
            </CardContent>
          </Card>

          {/* STAR bullet inputs */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Your Experience (Bullet Points)
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mb: 2 }}
              >
                Enter key facts for each component. The AI will weave these into
                a coherent narrative. Be specific — include numbers, team sizes,
                technologies, and outcomes.
              </Typography>

              <Stack spacing={3}>
                <TextField
                  fullWidth
                  multiline
                  minRows={3}
                  label="Situation"
                  placeholder={
                    "- At Company X, Q3 2023\n- ML pipeline serving 10M users\n- 12% failure rate in production"
                  }
                  value={situation}
                  onChange={(e) => setSituation(e.target.value)}
                  helperText="Context: Where, when, what was happening, what were the stakes?"
                />

                <TextField
                  fullWidth
                  multiline
                  minRows={2}
                  label="Task"
                  placeholder={
                    "- Owned root cause diagnosis\n- Had to fix before Black Friday"
                  }
                  value={task}
                  onChange={(e) => setTask(e.target.value)}
                  helperText="Your responsibility: What were you specifically asked to do?"
                />

                <TextField
                  fullWidth
                  multiline
                  minRows={3}
                  label="Action"
                  placeholder={
                    "- Built drift detection monitoring\n- Refactored validation layer\n- Ran A/B test on new pipeline"
                  }
                  value={action}
                  onChange={(e) => setAction(e.target.value)}
                  helperText="What YOU did (not the team): Steps, reasoning, trade-offs"
                />

                <TextField
                  fullWidth
                  multiline
                  minRows={2}
                  label="Result"
                  placeholder={
                    "- Failure rate: 12% → 0.3%\n- Saved $200K/quarter\n- Promoted to senior"
                  }
                  value={result}
                  onChange={(e) => setResult(e.target.value)}
                  helperText="Outcomes: Metrics, impact, what you learned"
                />
              </Stack>
            </CardContent>
          </Card>

          <Button
            variant="contained"
            size="large"
            fullWidth
            startIcon={
              phase === "generating" ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                <AutoAwesomeIcon />
              )
            }
            onClick={handleGenerate}
            disabled={!canGenerate || phase === "generating"}
          >
            {phase === "generating"
              ? "Generating your answer..."
              : "Generate STAR Answer"}
          </Button>
        </>
      )}

      {/* ---- Phase: Editing (review generated answer) ---- */}
      {(phase === "editing" || phase === "submitting") && (
        <>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                  mb: 2,
                }}
              >
                <EditIcon color="primary" />
                <Typography variant="h6">Review & Edit</Typography>
                <Box sx={{ flexGrow: 1 }} />
                {genStats && (
                  <Chip
                    label={`AI generated in ${genStats.processing_seconds}s`}
                    size="small"
                    color="secondary"
                    variant="outlined"
                  />
                )}
              </Box>

              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mb: 2 }}
              >
                Review the AI-generated answer below. Edit freely — make it sound
                like you. Your edits will be submitted for evaluation.
              </Typography>

              <TextField
                fullWidth
                multiline
                minRows={10}
                maxRows={20}
                value={editedText}
                onChange={(e) => setEditedText(e.target.value)}
                disabled={phase === "submitting"}
              />

              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 2,
                  mt: 1,
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  {wordCount} words
                </Typography>
                {wordCount < 100 && (
                  <Typography variant="body2" color="warning.main">
                    (Aim for 200-400 words)
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>

          {/* Context reminder */}
          <Card sx={{ mb: 3, bgcolor: "grey.50" }}>
            <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
              <Typography variant="body2" color="text.secondary">
                <strong>{selectedCompany?.name}</strong> &middot; {role} &middot;{" "}
                {level}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {questionText}
              </Typography>
            </CardContent>
          </Card>

          <Box sx={{ display: "flex", gap: 2 }}>
            <Button
              variant="outlined"
              onClick={() => {
                setPhase("input");
                setGeneratedText("");
                setEditedText("");
                setGenStats(null);
              }}
            >
              Start Over
            </Button>
            <Button
              variant="outlined"
              onClick={() => setEditedText(generatedText)}
              disabled={editedText === generatedText}
            >
              Reset to Original
            </Button>
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
              onClick={handleSubmitForEvaluation}
              disabled={
                phase === "submitting" || editedText.trim().length < 10
              }
            >
              {phase === "submitting"
                ? "Submitting..."
                : "Submit for Evaluation"}
            </Button>
          </Box>
        </>
      )}
    </Box>
  );
}
