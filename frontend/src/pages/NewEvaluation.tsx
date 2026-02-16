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

import React, { useCallback, useRef, useState } from "react";
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
  Collapse,
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
import UploadFileIcon from "@mui/icons-material/UploadFile";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import AssignmentIcon from "@mui/icons-material/Assignment";
import LinearProgress from "@mui/material/LinearProgress";

import {
  listCompanies,
  listQuestions,
  listTemplates,
  getTemplate,
  getRandomQuestion,
  createAnswer,
  createEvaluation,
  importAnswers,
  listScenarios,
  getRandomScenario,
  getScenarioCategories,
  Company,
  Question,
  Scenario,
  AnswerTemplate,
  ImportResponse,
} from "../api/client";
import UpgradePrompt, { isTierLimitError } from "../components/UpgradePrompt";
import VoiceInput from "../components/VoiceInput";

const TRACKS = [
  { value: "standard", label: "Standard (STAR)" },
  { value: "agentic", label: "Agentic AI Engineer" },
];

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
  const [track, setTrack] = useState("standard");
  const [companyId, setCompanyId] = useState("");
  const [role, setRole] = useState("");
  const [level, setLevel] = useState("");
  const [agenticCategory, setAgenticCategory] = useState("");
  const [agenticType, setAgenticType] = useState("behavioral");
  const [selectedScenarioId, setSelectedScenarioId] = useState("");

  const isAgentic = track === "agentic";
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

  // Import state
  const [importResult, setImportResult] = useState<ImportResponse | null>(null);
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Data queries
  const { data: companies = [], isLoading: loadingCompanies } = useQuery({
    queryKey: ["companies"],
    queryFn: listCompanies,
  });

  // Templates query — only fetch if user might be authenticated
  const { data: templates = [] } = useQuery({
    queryKey: ["templates"],
    queryFn: listTemplates,
    // Silently fail for unauthenticated users
    retry: false,
  });

  const { data: questionList, isLoading: loadingQuestions } = useQuery({
    queryKey: ["questions", role, level],
    queryFn: () =>
      listQuestions({
        role: role || undefined,
        level: level || undefined,
        limit: 100,
      }),
    enabled: questionMode === "bank" && !isAgentic,
  });

  // Agentic scenario queries
  const { data: scenarios } = useQuery({
    queryKey: ["scenarios", agenticCategory, agenticType],
    queryFn: () =>
      listScenarios({
        track: "agentic",
        category: agenticCategory || undefined,
        interview_type: agenticType || undefined,
      }),
    enabled: isAgentic,
  });

  const { data: categories = [] } = useQuery({
    queryKey: ["scenario-categories"],
    queryFn: () => getScenarioCategories("agentic"),
    enabled: isAgentic,
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
      // Determine question text for agentic scenarios
      let questionText: string | undefined;
      if (isAgentic && selectedScenarioId) {
        const scenario = scenarios?.items.find(
          (s) => s.id === selectedScenarioId
        );
        questionText = scenario?.question;
      }

      // Create answer — agentic track doesn't require company
      const answer = await createAnswer({
        question_id:
          !isAgentic && questionMode === "bank"
            ? selectedQuestionId
            : undefined,
        custom_question_text: isAgentic
          ? questionText || customQuestion || undefined
          : questionMode === "custom"
          ? customQuestion
          : undefined,
        target_company_id: isAgentic ? undefined : companyId,
        target_role: isAgentic ? "AGENTIC" : role,
        experience_level: isAgentic ? "senior" : level,
        answer_text: answerText,
        track: track,
        interview_type: isAgentic ? agenticType : "behavioral",
      } as any);

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

    if (isAgentic) {
      // Agentic validation — simpler, no company required
      if (!selectedScenarioId && !customQuestion.trim())
        return setError("Please select a scenario or enter a custom question.");
      if (answerText.trim().split(/\s+/).length < 10)
        return setError("Answer must be at least 10 words.");
    } else {
      // Standard validation
      if (!companyId) return setError("Please select a company.");
      if (!role) return setError("Please select a role.");
      if (!level) return setError("Please select an experience level.");
      if (questionMode === "bank" && !selectedQuestionId)
        return setError("Please select a question from the bank.");
      if (questionMode === "custom" && !customQuestion.trim())
        return setError("Please enter a custom question.");
      if (answerText.trim().split(/\s+/).length < 10)
        return setError("Answer must be at least 10 words.");
    }

    submitMutation.mutate();
  };

  // Import handlers
  const handleImportFile = useCallback(
    async (file: File) => {
      // Validate context first
      if (!companyId || !role || !level) {
        setImportError("Please select company, role, and experience level before importing.");
        return;
      }

      const validExts = [".txt", ".md"];
      const ext = file.name.toLowerCase().slice(file.name.lastIndexOf("."));
      if (!validExts.includes(ext)) {
        setImportError("Only .txt and .md files are supported.");
        return;
      }

      if (file.size > 100 * 1024) {
        setImportError("File exceeds 100KB limit.");
        return;
      }

      setImporting(true);
      setImportError(null);
      setImportResult(null);

      try {
        const result = await importAnswers(file, companyId, role, level);
        setImportResult(result);
      } catch (err: any) {
        const detail = err?.response?.data?.detail;
        setImportError(
          typeof detail === "string"
            ? detail
            : detail?.message || "Import failed. Please try again."
        );
      } finally {
        setImporting(false);
      }
    },
    [companyId, role, level]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleImportFile(file);
    },
    [handleImportFile]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleImportFile(file);
      // Reset input so same file can be re-selected
      if (fileInputRef.current) fileInputRef.current.value = "";
    },
    [handleImportFile]
  );

  const wordCount = answerText.trim()
    ? answerText.trim().split(/\s+/).length
    : 0;

  const selectedQuestion = questionList?.items.find(
    (q) => q.id === selectedQuestionId
  );

  // Progress calculation — rough step completion tracker
  const progressPct = (() => {
    let filled = 0;
    const total = 3;
    if (isAgentic) {
      if (agenticType) filled += 1;
      if (selectedScenarioId || customQuestion.trim()) filled += 1;
      if (answerText.trim().split(/\s+/).length >= 10) filled += 1;
    } else {
      if (companyId && role && level) filled += 1;
      if (
        (questionMode === "bank" && selectedQuestionId) ||
        (questionMode === "custom" && customQuestion.trim())
      )
        filled += 1;
      if (answerText.trim().split(/\s+/).length >= 10) filled += 1;
    }
    return (filled / total) * 100;
  })();

  return (
    <Box sx={{ maxWidth: 800, mx: "auto" }}>
      <Typography
        variant="h4"
        gutterBottom
        sx={{ fontSize: { xs: "1.5rem", sm: "2.125rem" } }}
      >
        New Evaluation
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
        {isAgentic
          ? "Practice agentic AI interview questions. Get scored on 4 dimensions with a Staff Engineer rewrite."
          : "Select your target company and role, choose a question, paste your STAR-formatted answer, and get AI-powered feedback."}
      </Typography>

      {/* Track Selector — pill-style toggle */}
      <Stack direction="row" spacing={1.5} sx={{ mb: 2 }}>
        <Card
          variant={track === "standard" ? "elevation" : "outlined"}
          sx={{
            flex: 1,
            cursor: "pointer",
            p: 0,
            border: 2,
            borderColor: track === "standard" ? "primary.main" : "divider",
            transition: "all 0.15s ease",
            "&:hover": {
              borderColor: track === "standard" ? "primary.main" : "primary.light",
            },
          }}
          onClick={() => setTrack("standard")}
        >
          <CardContent sx={{ py: 1.5, px: 2, "&:last-child": { pb: 1.5 } }}>
            <Stack direction="row" alignItems="center" spacing={1}>
              <AssignmentIcon
                sx={{ color: track === "standard" ? "primary.main" : "text.secondary", fontSize: 22 }}
              />
              <Box>
                <Typography variant="subtitle2" fontWeight={track === "standard" ? 700 : 500}>
                  Standard (STAR)
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  6-dimension behavioral scoring
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>
        <Card
          variant={track === "agentic" ? "elevation" : "outlined"}
          sx={{
            flex: 1,
            cursor: "pointer",
            p: 0,
            border: 2,
            borderColor: track === "agentic" ? "secondary.main" : "divider",
            transition: "all 0.15s ease",
            "&:hover": {
              borderColor: track === "agentic" ? "secondary.main" : "secondary.light",
            },
          }}
          onClick={() => setTrack("agentic")}
        >
          <CardContent sx={{ py: 1.5, px: 2, "&:last-child": { pb: 1.5 } }}>
            <Stack direction="row" alignItems="center" spacing={1}>
              <SmartToyIcon
                sx={{ color: track === "agentic" ? "secondary.main" : "text.secondary", fontSize: 22 }}
              />
              <Box sx={{ flex: 1 }}>
                <Stack direction="row" alignItems="center" spacing={0.75}>
                  <Typography variant="subtitle2" fontWeight={track === "agentic" ? 700 : 500}>
                    Agentic AI Engineer
                  </Typography>
                  <Chip
                    label="NEW"
                    size="small"
                    color="secondary"
                    sx={{ height: 18, fontSize: 10, fontWeight: 700 }}
                  />
                </Stack>
                <Typography variant="caption" color="text.secondary">
                  0-100 scoring + Staff Engineer rewrite
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      </Stack>

      {/* Progress indicator */}
      <Box sx={{ mb: 3 }}>
        <LinearProgress
          variant="determinate"
          value={progressPct}
          sx={{
            height: 4,
            borderRadius: 2,
            bgcolor: "grey.100",
            "& .MuiLinearProgress-bar": {
              borderRadius: 2,
              transition: "transform 0.4s ease",
              bgcolor: progressPct === 100 ? "secondary.main" : "primary.main",
            },
          }}
        />
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: "block" }}>
          {progressPct === 0
            ? "Fill in the steps below"
            : progressPct === 100
            ? "Ready to evaluate!"
            : `${Math.round(progressPct)}% complete`}
        </Typography>
      </Box>

      <Stack spacing={3}>
        {/* Context Selection — different for each track */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              1. {isAgentic ? "Interview Type" : "Target Context"}
            </Typography>
            <Stack spacing={2}>
              {isAgentic ? (
                /* Agentic track — type + category selectors */
                <Stack direction="row" spacing={2}>
                  <FormControl fullWidth>
                    <InputLabel>Type</InputLabel>
                    <Select
                      value={agenticType}
                      label="Type"
                      onChange={(e) => setAgenticType(e.target.value)}
                    >
                      <MenuItem value="behavioral">Behavioral</MenuItem>
                      <MenuItem value="system_design">System Design</MenuItem>
                    </Select>
                  </FormControl>
                  <FormControl fullWidth>
                    <InputLabel>Category (optional)</InputLabel>
                    <Select
                      value={agenticCategory}
                      label="Category (optional)"
                      onChange={(e) => setAgenticCategory(e.target.value)}
                    >
                      <MenuItem value="">All Categories</MenuItem>
                      {categories.map((c: string) => (
                        <MenuItem key={c} value={c}>
                          {c.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Stack>
              ) : (
                /* Standard track — company + role + level */
                <>
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
                </>
              )}
            </Stack>
          </CardContent>
        </Card>

        {/* Question Selection */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              2. {isAgentic ? "Agentic Scenario" : "Behavioral Question"}
            </Typography>

            {isAgentic ? (
              /* Agentic scenario selector */
              <Stack spacing={2}>
                <FormControl fullWidth>
                  <InputLabel>Select a Scenario</InputLabel>
                  <Select
                    value={selectedScenarioId}
                    label="Select a Scenario"
                    onChange={(e) => setSelectedScenarioId(e.target.value)}
                  >
                    {scenarios?.items.map((s: Scenario) => (
                      <MenuItem key={s.id} value={s.id}>
                        <Box>
                          <Typography variant="body2" sx={{ maxWidth: 600, whiteSpace: "normal" }}>
                            {s.question}
                          </Typography>
                          <Stack direction="row" spacing={0.5} sx={{ mt: 0.5 }}>
                            <Chip
                              label={s.category.replace(/_/g, " ")}
                              size="small"
                              variant="outlined"
                            />
                            <Chip
                              label={s.difficulty}
                              size="small"
                              color={s.difficulty === "expert" ? "error" : "warning"}
                            />
                            <Chip
                              label={s.type === "system_design" ? "System Design" : "Behavioral"}
                              size="small"
                              color="primary"
                              variant="outlined"
                            />
                          </Stack>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                {selectedScenarioId && scenarios?.items.find(s => s.id === selectedScenarioId) && (
                  <Alert severity="info">
                    <strong>Selected:</strong>{" "}
                    {scenarios.items.find(s => s.id === selectedScenarioId)!.question}
                  </Alert>
                )}

                <Typography variant="body2" color="text.secondary">
                  Or type a custom agentic question below:
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  minRows={2}
                  label="Custom question (optional)"
                  value={customQuestion}
                  onChange={(e) => {
                    setCustomQuestion(e.target.value);
                    if (e.target.value) setSelectedScenarioId("");
                  }}
                  placeholder="Design an agent that..."
                />
              </Stack>
            ) : (
            <>
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
            </>
            )}
          </CardContent>
        </Card>

        {/* Answer Input */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              3. {isAgentic ? "Your Answer" : "Your STAR Answer"}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {isAgentic
                ? "Describe your approach to the scenario. Be specific about architecture, safety considerations, and trade-offs. Aim for 200-500 words."
                : "Paste your answer using the STAR framework: Situation, Task, Action, Result. Aim for 200-400 words (about 2-3 minutes spoken)."}
            </Typography>

            {/* Template selector */}
            {templates.length > 0 && (
              <FormControl fullWidth sx={{ mb: 2 }} size="small">
                <InputLabel>Load from Template</InputLabel>
                <Select
                  value=""
                  label="Load from Template"
                  onChange={async (e) => {
                    const templateId = e.target.value as string;
                    if (!templateId) return;
                    try {
                      const tmpl = await getTemplate(templateId);
                      setAnswerText(tmpl.template_text);
                    } catch {
                      // Silently fail — user can still type manually
                    }
                  }}
                >
                  {templates.map((t: AnswerTemplate) => (
                    <MenuItem key={t.id} value={t.id}>
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <Typography variant="body2">{t.name}</Typography>
                        {t.is_default && (
                          <Chip label="Default" size="small" color="primary" variant="outlined" />
                        )}
                      </Stack>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}

            <TextField
              fullWidth
              multiline
              minRows={8}
              maxRows={20}
              value={answerText}
              onChange={(e) => setAnswerText(e.target.value)}
              placeholder={
                isAgentic
                  ? "I would approach this by first defining the agent's goals and constraints...\n\n" +
                    "The architecture would use...\n\n" +
                    "For safety, I would implement...\n\n" +
                    "Key trade-offs include..."
                  : "Situation: At my previous company...\n\n" +
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

        {/* Bulk Import */}
        <Card variant="outlined">
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Or Import from File
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Upload a .txt or .md file with one or more STAR answers.
              Separate multiple answers with --- or ===. Optionally prefix
              each with "## Question: ..."
            </Typography>

            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.md"
              style={{ display: "none" }}
              onChange={handleFileSelect}
            />

            {/* Drop zone */}
            <Box
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              sx={{
                border: 2,
                borderStyle: "dashed",
                borderColor: dragOver ? "primary.main" : "divider",
                borderRadius: 2,
                p: 3,
                textAlign: "center",
                cursor: "pointer",
                bgcolor: dragOver ? "primary.50" : "transparent",
                transition: "all 0.2s",
                "&:hover": {
                  borderColor: "primary.light",
                  bgcolor: "action.hover",
                },
              }}
            >
              {importing ? (
                <CircularProgress size={32} />
              ) : (
                <>
                  <UploadFileIcon
                    sx={{ fontSize: 40, color: "text.secondary", mb: 1 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    Drag & drop a file here, or click to browse
                  </Typography>
                  <Typography variant="caption" color="text.disabled">
                    .txt or .md — max 100KB
                  </Typography>
                </>
              )}
            </Box>

            {/* Import error */}
            {importError && (
              <Alert severity="error" sx={{ mt: 2 }} onClose={() => setImportError(null)}>
                {importError}
              </Alert>
            )}

            {/* Import result */}
            <Collapse in={!!importResult}>
              {importResult && (
                <Alert
                  severity="success"
                  icon={<CheckCircleIcon />}
                  sx={{ mt: 2 }}
                >
                  <Typography variant="subtitle2">
                    Imported {importResult.imported_count} of{" "}
                    {importResult.total_found} answer
                    {importResult.total_found !== 1 ? "s" : ""}
                  </Typography>
                  {importResult.answers.map((a) => (
                    <Typography key={a.answer_id} variant="body2">
                      • {a.question_text || "Custom answer"} ({a.word_count} words)
                    </Typography>
                  ))}
                  {importResult.errors.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" color="warning.main">
                        Warnings: {importResult.errors.join("; ")}
                      </Typography>
                    </Box>
                  )}
                </Alert>
              )}
            </Collapse>
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
          sx={{
            py: 1.5,
            px: 4,
            fontSize: "1rem",
            background: isAgentic
              ? "linear-gradient(135deg, #276749 0%, #38a169 100%)"
              : "linear-gradient(135deg, #1a365d 0%, #2b6cb0 100%)",
            "&:hover": {
              background: isAgentic
                ? "linear-gradient(135deg, #22543d 0%, #276749 100%)"
                : "linear-gradient(135deg, #0d1f3c 0%, #1a365d 100%)",
            },
          }}
        >
          {submitMutation.isPending
            ? "Evaluating..."
            : isAgentic
            ? "Evaluate with Agentic Criteria"
            : "Evaluate My Answer"}
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
