/**
 * New Evaluation page — the core user flow.
 *
 * Steps:
 * 1. Select company from dropdown (loads principles)
 * 2. Select role (MLE, PM, TPM, EM)
 * 3. Select experience level
 * 4. Pick a question (from bank or type custom)
 * 5. Paste STAR-formatted answer
 * 6. Submit → navigate to EvaluationDetail
 *
 * Uses plain useState for form state, validation on submit.
 */

import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
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
import SendIcon from "@mui/icons-material/Send";
import ShuffleIcon from "@mui/icons-material/Shuffle";

import {
  listCompanies,
  listQuestions,
  getRandomQuestion,
  createAnswer,
  createEvaluation,
  Company,
  Question,
} from "../api/client";
import UpgradePrompt, { isTierLimitError } from "../components/UpgradePrompt";
import VoiceInput from "../components/VoiceInput";

const ROLES = ["MLE", "PM", "TPM", "EM"];
const LEVELS = [
  { value: "entry", label: "Entry Level (L3/L4)" },
  { value: "mid", label: "Mid Level (L4/L5)" },
  { value: "senior", label: "Senior (L5/L6)" },
  { value: "staff", label: "Staff+ (L6/L7)" },
  { value: "manager", label: "Manager" },
];

export default function NewEvaluation() {
  const navigate = useNavigate();
  const location = useLocation();
  const passedQuestionId = (location.state as any)?.questionId || "";

  // Form state
  const [companyId, setCompanyId] = useState("");
  const [role, setRole] = useState("");
  const [level, setLevel] = useState("");
  const [questionMode, setQuestionMode] = useState<"bank" | "custom">("bank");
  const [selectedQuestionId, setSelectedQuestionId] = useState(passedQuestionId);
  const [customQuestion, setCustomQuestion] = useState("");
  const [answerText, setAnswerText] = useState("");
  const [error, setError] = useState("");
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [tierLimitInfo, setTierLimitInfo] = useState<{
    currentUsage?: number;
    limit?: number;
  }>({});

  // Data queries
  const { data: companies = [], isLoading: loadingCompanies } = useQuery({
    queryKey: ["companies"],
    queryFn: listCompanies,
  });

  const { data: questionList, isLoading: loadingQuestions } = useQuery({
    queryKey: ["questions", role, level],
    queryFn: () =>
      listQuestions({
        role: role || undefined,
        level: level || undefined,
        limit: 100,
      }),
    enabled: questionMode === "bank",
  });

  // Random question
  const randomMutation = useMutation({
    mutationFn: () =>
      getRandomQuestion({
        role: role || undefined,
        level: level || undefined,
      }),
    onSuccess: (q: Question) => {
      setSelectedQuestionId(q.id);
    },
  });

  // Submit mutation
  const submitMutation = useMutation({
    mutationFn: async () => {
      // Create answer
      const answer = await createAnswer({
        question_id: questionMode === "bank" ? selectedQuestionId : undefined,
        custom_question_text:
          questionMode === "custom" ? customQuestion : undefined,
        target_company_id: companyId,
        target_role: role,
        experience_level: level,
        answer_text: answerText,
      });

      // Get the first version's ID
      // The answer response doesn't include versions, so we need to
      // create the evaluation using the answer detail endpoint
      const answerDetail = await import("../api/client").then((m) =>
        m.getAnswer(answer.id)
      );
      const versionId = answerDetail.versions![0].id;

      // Create evaluation
      const evaluation = await createEvaluation(versionId);
      return evaluation;
    },
    onSuccess: (evaluation) => {
      navigate(`/evaluations/${evaluation.id}`);
    },
    onError: (err: any) => {
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
          : detail?.message || "Failed to submit. Please try again."
      );
    },
  });

  const handleSubmit = () => {
    setError("");

    // Validation
    if (!companyId) return setError("Please select a company.");
    if (!role) return setError("Please select a role.");
    if (!level) return setError("Please select an experience level.");
    if (questionMode === "bank" && !selectedQuestionId)
      return setError("Please select a question from the bank.");
    if (questionMode === "custom" && !customQuestion.trim())
      return setError("Please enter a custom question.");
    if (answerText.trim().split(/\s+/).length < 10)
      return setError("Answer must be at least 10 words.");

    submitMutation.mutate();
  };

  const wordCount = answerText.trim()
    ? answerText.trim().split(/\s+/).length
    : 0;

  const selectedQuestion = questionList?.items.find(
    (q) => q.id === selectedQuestionId
  );

  return (
    <Box sx={{ maxWidth: 800, mx: "auto" }}>
      <Typography
        variant="h4"
        gutterBottom
        sx={{ fontSize: { xs: "1.5rem", sm: "2.125rem" } }}
      >
        New Evaluation
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Select your target company and role, choose a question, paste your
        STAR-formatted answer, and get AI-powered feedback.
      </Typography>

      <Stack spacing={3}>
        {/* Company Selection */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              1. Target Context
            </Typography>
            <Stack spacing={2}>
              <FormControl fullWidth>
                <InputLabel>Company</InputLabel>
                <Select
                  value={companyId}
                  label="Company"
                  onChange={(e) => setCompanyId(e.target.value)}
                  disabled={loadingCompanies}
                >
                  {companies.map((c: Company) => (
                    <MenuItem key={c.id} value={c.id}>
                      {c.name}{" "}
                      <Typography
                        component="span"
                        variant="caption"
                        color="text.secondary"
                        sx={{ ml: 1 }}
                      >
                        ({c.principle_type})
                      </Typography>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Stack direction="row" spacing={2}>
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
              </Stack>
            </Stack>
          </CardContent>
        </Card>

        {/* Question Selection */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              2. Behavioral Question
            </Typography>

            <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
              <Chip
                label="From Question Bank"
                variant={questionMode === "bank" ? "filled" : "outlined"}
                color={questionMode === "bank" ? "primary" : "default"}
                onClick={() => setQuestionMode("bank")}
              />
              <Chip
                label="Custom Question"
                variant={questionMode === "custom" ? "filled" : "outlined"}
                color={questionMode === "custom" ? "primary" : "default"}
                onClick={() => setQuestionMode("custom")}
              />
            </Stack>

            {questionMode === "bank" ? (
              <Stack spacing={2}>
                <FormControl fullWidth>
                  <InputLabel>Select a Question</InputLabel>
                  <Select
                    value={selectedQuestionId}
                    label="Select a Question"
                    onChange={(e) => setSelectedQuestionId(e.target.value)}
                    disabled={loadingQuestions}
                  >
                    {questionList?.items.map((q: Question) => (
                      <MenuItem key={q.id} value={q.id}>
                        <Box>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 600 }}>
                            {q.question_text}
                          </Typography>
                          <Stack direction="row" spacing={0.5} sx={{ mt: 0.5 }}>
                            {q.competency_tags.slice(0, 2).map((t) => (
                              <Chip key={t} label={t} size="small" variant="outlined" />
                            ))}
                            <Chip
                              label={q.difficulty}
                              size="small"
                              color={
                                q.difficulty === "advanced"
                                  ? "warning"
                                  : q.difficulty === "senior_plus"
                                  ? "error"
                                  : "default"
                              }
                            />
                          </Stack>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <Button
                  variant="outlined"
                  startIcon={<ShuffleIcon />}
                  onClick={() => randomMutation.mutate()}
                  disabled={randomMutation.isPending}
                  size="small"
                >
                  Surprise Me
                </Button>

                {selectedQuestion && (
                  <Alert severity="info" sx={{ mt: 1 }}>
                    <strong>Selected:</strong> {selectedQuestion.question_text}
                  </Alert>
                )}
              </Stack>
            ) : (
              <TextField
                fullWidth
                multiline
                minRows={2}
                label="Type your behavioral question"
                value={customQuestion}
                onChange={(e) => setCustomQuestion(e.target.value)}
                placeholder="Tell me about a time when..."
              />
            )}
          </CardContent>
        </Card>

        {/* Answer Input */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              3. Your STAR Answer
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Paste your answer using the STAR framework: Situation, Task,
              Action, Result. Aim for 200-400 words (about 2-3 minutes spoken).
            </Typography>
            <TextField
              fullWidth
              multiline
              minRows={8}
              maxRows={20}
              value={answerText}
              onChange={(e) => setAnswerText(e.target.value)}
              placeholder={
                "Situation: At my previous company...\n\n" +
                "Task: I was responsible for...\n\n" +
                "Action: I decided to...\n\n" +
                "Result: As a result..."
              }
            />
            <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mt: 1 }}>
              <VoiceInput
                onTranscript={(text) =>
                  setAnswerText((prev) =>
                    prev ? prev.trimEnd() + " " + text : text
                  )
                }
                disabled={submitMutation.isPending}
              />
              <Typography
                variant="caption"
                color={
                  wordCount < 50
                    ? "error"
                    : wordCount > 500
                    ? "warning.main"
                    : "text.secondary"
                }
              >
                {wordCount} words
                {wordCount < 50 && " — aim for at least 100 words"}
                {wordCount > 500 && " — consider trimming for interview delivery"}
              </Typography>
            </Box>
          </CardContent>
        </Card>

        {/* Error Display */}
        {error && (
          <Alert severity="error" onClose={() => setError("")}>
            {error}
          </Alert>
        )}

        {/* Submit */}
        <Button
          variant="contained"
          size="large"
          endIcon={
            submitMutation.isPending ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              <SendIcon />
            )
          }
          onClick={handleSubmit}
          disabled={submitMutation.isPending}
          sx={{ py: 1.5 }}
        >
          {submitMutation.isPending ? "Evaluating..." : "Evaluate My Answer"}
        </Button>
      </Stack>

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
