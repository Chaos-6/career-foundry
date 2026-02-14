/**
 * Evaluation Detail page — shows scores, full feedback, and revision flow.
 *
 * Polls the evaluation status until it transitions to 'completed' or 'failed'.
 * Then renders:
 * - 6-dimension score bars
 * - AI-powered improvement suggestions for weak dimensions (≤3)
 * - Full evaluation markdown
 * - PDF download button
 * - "Revise & Re-Evaluate" inline editor
 *
 * Revision flow:
 * 1. User clicks "Revise & Re-Evaluate"
 * 2. Editor opens pre-populated with the evaluated answer text
 * 3. User edits their answer based on feedback
 * 4. Submit creates a new AnswerVersion + Evaluation and navigates to it
 */

import React, { useState } from "react";
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
  Collapse,
  Divider,
  Grid,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import CheckIcon from "@mui/icons-material/Check";
import DownloadIcon from "@mui/icons-material/Download";
import EditIcon from "@mui/icons-material/Edit";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import LinkOffIcon from "@mui/icons-material/LinkOff";
import SendIcon from "@mui/icons-material/Send";
import ShareIcon from "@mui/icons-material/Share";
import CompareArrowsIcon from "@mui/icons-material/CompareArrows";
import CloseIcon from "@mui/icons-material/Close";
import BookmarkAddIcon from "@mui/icons-material/BookmarkAdd";
import AutoFixHighIcon from "@mui/icons-material/AutoFixHigh";
import LightbulbIcon from "@mui/icons-material/Lightbulb";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

import {
  getEvaluation,
  getEvaluationPdfUrl,
  createVersion,
  createEvaluation,
  shareEvaluation,
  revokeShare,
  createTemplate,
  getEvaluationSuggestions,
  SuggestionItem,
} from "../api/client";
import ScoreBar from "../components/ScoreBar";
import SimpleMarkdown from "../components/SimpleMarkdown";
import PageLoader from "../components/PageLoader";
import UpgradePrompt, { isTierLimitError } from "../components/UpgradePrompt";

export default function EvaluationDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Revision state
  const [revising, setRevising] = useState(false);
  const [revisedText, setRevisedText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [revisionError, setRevisionError] = useState<string | null>(null);
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [tierLimitInfo, setTierLimitInfo] = useState<{
    currentUsage?: number;
    limit?: number;
  }>({});

  // Share state
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [sharing, setSharing] = useState(false);
  const [copied, setCopied] = useState(false);

  // Save as template state
  const [savedAsTemplate, setSavedAsTemplate] = useState(false);
  const [savingTemplate, setSavingTemplate] = useState(false);

  // Inline suggestions state
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);
  const [suggestionsMessage, setSuggestionsMessage] = useState<string | null>(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [suggestionsLoaded, setSuggestionsLoaded] = useState(false);
  const [suggestionsExpanded, setSuggestionsExpanded] = useState(true);

  const {
    data: evaluation,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["evaluation", id],
    queryFn: () => getEvaluation(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 2000;
      if (data.status === "completed" || data.status === "failed") return false;
      return 2000;
    },
  });

  // Open revision editor with the current answer pre-populated
  const handleStartRevise = () => {
    if (evaluation?.answer_text) {
      setRevisedText(evaluation.answer_text);
    }
    setRevisionError(null);
    setRevising(true);
  };

  // Submit revised answer: create new version → create evaluation → navigate
  const handleSubmitRevision = async () => {
    if (!evaluation?.answer_id) {
      setRevisionError("Cannot revise: missing answer context.");
      return;
    }
    if (revisedText.trim().split(/\s+/).length < 10) {
      setRevisionError("Your revised answer must be at least 10 words.");
      return;
    }
    if (revisedText.trim() === evaluation.answer_text?.trim()) {
      setRevisionError(
        "Your revision is identical to the original. Make changes based on the feedback above."
      );
      return;
    }

    setSubmitting(true);
    setRevisionError(null);

    try {
      // 1. Create new version
      const newVersion = await createVersion(evaluation.answer_id, {
        answer_text: revisedText.trim(),
      });

      // 2. Kick off evaluation on the new version
      const newEval = await createEvaluation(newVersion.id);

      // 3. Navigate to the new evaluation (will show polling → results)
      navigate(`/evaluations/${newEval.id}`, { replace: false });
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
      const detail = err?.response?.data?.detail;
      const msg =
        typeof detail === "string"
          ? detail
          : detail?.message || err?.message || "Failed to submit revision.";
      setRevisionError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  // Share or copy existing share link
  const handleShare = async () => {
    if (!evaluation) return;

    // If already shared, just copy the URL
    if (shareUrl) {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      return;
    }

    setSharing(true);
    try {
      const result = await shareEvaluation(evaluation.id);
      setShareUrl(result.share_url);
      await navigator.clipboard.writeText(result.share_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      refetch(); // refresh to show share_token in evaluation data
    } catch {
      // Silently fail — the button will remain available to retry
    } finally {
      setSharing(false);
    }
  };

  // Revoke sharing
  const handleRevokeShare = async () => {
    if (!evaluation) return;
    try {
      await revokeShare(evaluation.id);
      setShareUrl(null);
      refetch();
    } catch {
      // Silently fail
    }
  };

  // Save as template
  const handleSaveAsTemplate = async () => {
    if (!evaluation?.answer_text) return;
    setSavingTemplate(true);
    try {
      await createTemplate({
        name: `Template from evaluation ${new Date().toLocaleDateString()}`,
        template_text: evaluation.answer_text,
      });
      setSavedAsTemplate(true);
    } catch {
      // Silently fail — button stays available for retry
    } finally {
      setSavingTemplate(false);
    }
  };

  // Load AI-powered suggestions for weak dimensions
  const handleLoadSuggestions = async () => {
    if (!evaluation || suggestionsLoaded) return;
    setLoadingSuggestions(true);
    try {
      const result = await getEvaluationSuggestions(evaluation.id);
      setSuggestions(result.suggestions);
      setSuggestionsMessage(result.message || null);
      setSuggestionsLoaded(true);
    } catch {
      setSuggestionsMessage("Failed to load suggestions. Please try again.");
    } finally {
      setLoadingSuggestions(false);
    }
  };

  // Check if any dimension scored ≤3 (suggestions are relevant)
  const hasWeakDimensions =
    evaluation?.status === "completed" &&
    [
      evaluation.situation_score,
      evaluation.task_score,
      evaluation.action_score,
      evaluation.result_score,
      evaluation.engagement_score,
      evaluation.overall_score,
    ].some((score) => score !== null && score <= 3);

  if (isLoading) {
    return <PageLoader message="Loading evaluation..." />;
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

  // Word count for revision
  const wordCount = revisedText.trim().split(/\s+/).filter(Boolean).length;

  // --- Completed state ---
  return (
    <Box sx={{ maxWidth: 900, mx: "auto" }}>
      {/* Header */}
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        sx={{ mb: 3 }}
      >
        <Box>
          <Typography
            variant="h4"
            gutterBottom
            sx={{ fontSize: { xs: "1.4rem", sm: "2.125rem" } }}
          >
            Evaluation Results
            {evaluation.version_number && (
              <Chip
                label={`v${evaluation.version_number}`}
                size="small"
                sx={{ ml: 1, verticalAlign: "middle" }}
              />
            )}
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap">
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
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={1}
          flexWrap="wrap"
          sx={{ width: { xs: "100%", sm: "auto" } }}
        >
          <Button
            variant="contained"
            color="secondary"
            startIcon={<EditIcon />}
            onClick={handleStartRevise}
            disabled={!evaluation.answer_id || revising}
            fullWidth={false}
          >
            Revise & Re-Evaluate
          </Button>
          {evaluation.answer_id && (
            <Button
              variant="outlined"
              startIcon={<CompareArrowsIcon />}
              onClick={() =>
                navigate(`/answers/${evaluation.answer_id}/compare`)
              }
            >
              Compare Versions
            </Button>
          )}
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            href={getEvaluationPdfUrl(evaluation.id)}
            target="_blank"
          >
            PDF
          </Button>
          <Button
            variant={shareUrl || evaluation.share_token ? "contained" : "outlined"}
            color={copied ? "success" : "primary"}
            startIcon={
              sharing ? (
                <CircularProgress size={18} color="inherit" />
              ) : copied ? (
                <CheckIcon />
              ) : (
                <ShareIcon />
              )
            }
            onClick={handleShare}
            disabled={sharing}
          >
            {copied
              ? "Copied!"
              : shareUrl || evaluation.share_token
              ? "Copy Link"
              : "Share"}
          </Button>
          {evaluation.answer_text && (
            <Button
              variant="outlined"
              startIcon={
                savingTemplate ? (
                  <CircularProgress size={18} color="inherit" />
                ) : savedAsTemplate ? (
                  <CheckIcon />
                ) : (
                  <BookmarkAddIcon />
                )
              }
              onClick={handleSaveAsTemplate}
              disabled={savingTemplate || savedAsTemplate}
              color={savedAsTemplate ? "success" : "primary"}
            >
              {savedAsTemplate ? "Saved!" : "Save as Template"}
            </Button>
          )}
          {(shareUrl || evaluation.share_token) && (
            <Button
              variant="text"
              size="small"
              startIcon={<LinkOffIcon />}
              onClick={handleRevokeShare}
              color="error"
              sx={{ minWidth: "auto" }}
            >
              Revoke
            </Button>
          )}
        </Stack>
      </Stack>

      {/* Revision Editor — collapsible panel */}
      <Collapse in={revising}>
        <Card
          sx={{
            mb: 3,
            border: 2,
            borderColor: "secondary.main",
            bgcolor: "secondary.50",
          }}
        >
          <CardContent>
            <Stack
              direction="row"
              justifyContent="space-between"
              alignItems="center"
              sx={{ mb: 2 }}
            >
              <Typography variant="h6" color="secondary.dark">
                Revise Your Answer
              </Typography>
              <Button
                size="small"
                startIcon={<CloseIcon />}
                onClick={() => setRevising(false)}
                color="inherit"
              >
                Cancel
              </Button>
            </Stack>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Edit your answer below based on the feedback. Focus on the weakest
              dimension scores. Your original answer is pre-loaded — modify it
              and submit to create a new version with a fresh evaluation.
            </Typography>

            <TextField
              multiline
              minRows={8}
              maxRows={20}
              fullWidth
              value={revisedText}
              onChange={(e) => setRevisedText(e.target.value)}
              placeholder="Edit your STAR answer here..."
              sx={{
                mb: 1,
                "& .MuiOutlinedInput-root": { bgcolor: "white" },
              }}
            />

            <Stack
              direction="row"
              justifyContent="space-between"
              alignItems="center"
            >
              <Typography variant="caption" color="text.secondary">
                {wordCount} words
                {wordCount < 100 && " (aim for 200-400 words)"}
              </Typography>
              <Stack direction="row" spacing={1}>
                {revisionError && (
                  <Alert severity="error" sx={{ py: 0 }}>
                    {revisionError}
                  </Alert>
                )}
                <Button
                  variant="contained"
                  color="secondary"
                  startIcon={
                    submitting ? (
                      <CircularProgress size={18} color="inherit" />
                    ) : (
                      <SendIcon />
                    )
                  }
                  onClick={handleSubmitRevision}
                  disabled={submitting || wordCount < 10}
                >
                  {submitting ? "Submitting..." : "Submit Revision"}
                </Button>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Collapse>

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

          {/* AI Improvement Suggestions */}
          {hasWeakDimensions && (
            <Card
              sx={{
                mt: 2,
                border: 1,
                borderColor: "info.light",
                bgcolor: "info.50",
              }}
            >
              <CardContent>
                <Stack
                  direction="row"
                  justifyContent="space-between"
                  alignItems="center"
                  sx={{ mb: suggestionsLoaded && suggestions.length > 0 ? 1 : 0 }}
                >
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <AutoFixHighIcon color="info" />
                    <Typography variant="h6" color="info.dark">
                      How to Improve
                    </Typography>
                  </Stack>
                  {!suggestionsLoaded && (
                    <Button
                      size="small"
                      variant="contained"
                      color="info"
                      startIcon={
                        loadingSuggestions ? (
                          <CircularProgress size={16} color="inherit" />
                        ) : (
                          <LightbulbIcon />
                        )
                      }
                      onClick={handleLoadSuggestions}
                      disabled={loadingSuggestions}
                    >
                      {loadingSuggestions ? "Thinking..." : "Get AI Tips"}
                    </Button>
                  )}
                  {suggestionsLoaded && suggestions.length > 0 && (
                    <Button
                      size="small"
                      onClick={() => setSuggestionsExpanded(!suggestionsExpanded)}
                      endIcon={
                        <ExpandMoreIcon
                          sx={{
                            transform: suggestionsExpanded
                              ? "rotate(180deg)"
                              : "rotate(0deg)",
                            transition: "transform 0.2s",
                          }}
                        />
                      }
                    >
                      {suggestionsExpanded ? "Hide" : "Show"}
                    </Button>
                  )}
                </Stack>

                {!suggestionsLoaded && !loadingSuggestions && (
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Get targeted AI tips for your weakest dimensions.
                  </Typography>
                )}

                {suggestionsMessage && suggestions.length === 0 && (
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {suggestionsMessage}
                  </Typography>
                )}

                <Collapse in={suggestionsExpanded}>
                  <Stack spacing={1.5} sx={{ mt: suggestions.length > 0 ? 1 : 0 }}>
                    {suggestions.map((s, i) => (
                      <Paper
                        key={i}
                        elevation={0}
                        sx={{ p: 1.5, bgcolor: "background.paper", borderRadius: 1 }}
                      >
                        <Chip
                          label={s.section.charAt(0).toUpperCase() + s.section.slice(1)}
                          size="small"
                          color="info"
                          sx={{ mb: 0.5, fontWeight: 600 }}
                        />
                        <Typography variant="body2" sx={{ mb: 0.5 }}>
                          {s.suggestion}
                        </Typography>
                        {s.example && (
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{
                              fontStyle: "italic",
                              pl: 1.5,
                              borderLeft: 2,
                              borderColor: "info.light",
                            }}
                          >
                            {s.example}
                          </Typography>
                        )}
                      </Paper>
                    ))}
                  </Stack>
                </Collapse>
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
