/**
 * Moderation Queue page — moderator-only view for reviewing community questions.
 *
 * Shows pending community question submissions in a FIFO queue.
 * Moderators can approve (adds to public bank) or reject (with required reason).
 *
 * Design:
 * - Each pending question shown as a card with full metadata
 * - Approve button is one-click (optional notes)
 * - Reject button requires a reason (helps submitters understand why)
 * - After action, card is removed from the list with an optimistic update
 */

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Skeleton,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CancelIcon from "@mui/icons-material/Cancel";
import GavelIcon from "@mui/icons-material/Gavel";
import InboxIcon from "@mui/icons-material/Inbox";

import {
  getPendingQuestions,
  moderateQuestion,
  ModerationQuestion,
} from "../api/client";

export default function ModerationQueue() {
  const queryClient = useQueryClient();
  const [rejectTarget, setRejectTarget] = useState<ModerationQuestion | null>(
    null
  );
  const [rejectNotes, setRejectNotes] = useState("");
  const [rejectError, setRejectError] = useState("");
  const [actionFeedback, setActionFeedback] = useState("");

  const {
    data: pending = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ["moderation-pending"],
    queryFn: () => getPendingQuestions(),
  });

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: (questionId: string) =>
      moderateQuestion(questionId, { action: "approve" }),
    onSuccess: (_, questionId) => {
      queryClient.setQueryData<ModerationQuestion[]>(
        ["moderation-pending"],
        (old) => old?.filter((q) => q.id !== questionId) ?? []
      );
      setActionFeedback("Question approved and added to the public bank.");
      setTimeout(() => setActionFeedback(""), 3000);
    },
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: ({
      questionId,
      notes,
    }: {
      questionId: string;
      notes: string;
    }) => moderateQuestion(questionId, { action: "reject", notes }),
    onSuccess: (_, { questionId }) => {
      queryClient.setQueryData<ModerationQuestion[]>(
        ["moderation-pending"],
        (old) => old?.filter((q) => q.id !== questionId) ?? []
      );
      setRejectTarget(null);
      setRejectNotes("");
      setRejectError("");
      setActionFeedback("Question rejected.");
      setTimeout(() => setActionFeedback(""), 3000);
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      setRejectError(
        typeof detail === "string" ? detail : "Failed to reject. Try again."
      );
    },
  });

  const handleReject = () => {
    if (!rejectNotes.trim()) {
      setRejectError("A rejection reason is required.");
      return;
    }
    if (!rejectTarget) return;
    rejectMutation.mutate({
      questionId: rejectTarget.id,
      notes: rejectNotes,
    });
  };

  return (
    <Box sx={{ maxWidth: 800, mx: "auto" }}>
      {/* Header */}
      <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 1 }}>
        <GavelIcon color="primary" fontSize="large" />
        <Typography
          variant="h4"
          sx={{ fontSize: { xs: "1.5rem", sm: "2.125rem" } }}
        >
          Moderation Queue
        </Typography>
      </Stack>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Review community-submitted questions. Approved questions appear in the
        public Question Bank.
      </Typography>

      {/* Feedback */}
      {actionFeedback && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {actionFeedback}
        </Alert>
      )}

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load pending questions. Are you a moderator?
        </Alert>
      )}

      {/* Loading */}
      {isLoading && (
        <Stack spacing={2}>
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent>
                <Skeleton variant="text" width="80%" height={28} />
                <Skeleton variant="text" width="50%" height={20} sx={{ mt: 1 }} />
                <Skeleton
                  variant="rectangular"
                  height={36}
                  sx={{ mt: 2, borderRadius: 1 }}
                />
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}

      {/* Empty state */}
      {!isLoading && pending.length === 0 && !error && (
        <Card>
          <CardContent sx={{ textAlign: "center", py: 6 }}>
            <InboxIcon sx={{ fontSize: 48, color: "text.disabled", mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              No questions pending review
            </Typography>
            <Typography variant="body2" color="text.secondary">
              All community submissions have been processed. Check back later!
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Pending questions */}
      <Stack spacing={2}>
        {pending.map((q) => (
          <Card key={q.id} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              {/* Question text */}
              <Typography variant="body1" sx={{ fontWeight: 500, mb: 1 }}>
                {q.question_text}
              </Typography>

              {/* Tags */}
              <Stack
                direction="row"
                spacing={0.5}
                flexWrap="wrap"
                useFlexGap
                sx={{ mb: 1.5 }}
              >
                {q.role_tags.map((t) => (
                  <Chip key={`r-${t}`} label={t} size="small" color="primary" variant="outlined" />
                ))}
                {q.competency_tags.map((t) => (
                  <Chip
                    key={`c-${t}`}
                    label={t.replace(/_/g, " ")}
                    size="small"
                    variant="outlined"
                  />
                ))}
                <Chip
                  label={q.difficulty.replace("_", " ")}
                  size="small"
                  color={
                    q.difficulty === "advanced"
                      ? "warning"
                      : q.difficulty === "senior_plus"
                      ? "error"
                      : "default"
                  }
                />
                {q.level_band && (
                  <Chip label={q.level_band} size="small" color="info" variant="outlined" />
                )}
              </Stack>

              {/* Submitter info */}
              <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 1.5 }}>
                Submitted by: {q.submitted_by_email || "Unknown"}
                {q.created_at &&
                  ` on ${new Date(q.created_at).toLocaleDateString()}`}
              </Typography>

              {/* Action buttons */}
              <Stack direction="row" spacing={1}>
                <Button
                  variant="contained"
                  color="success"
                  size="small"
                  startIcon={
                    approveMutation.isPending ? (
                      <CircularProgress size={16} color="inherit" />
                    ) : (
                      <CheckCircleIcon />
                    )
                  }
                  onClick={() => approveMutation.mutate(q.id)}
                  disabled={approveMutation.isPending}
                >
                  Approve
                </Button>
                <Button
                  variant="outlined"
                  color="error"
                  size="small"
                  startIcon={<CancelIcon />}
                  onClick={() => {
                    setRejectTarget(q);
                    setRejectNotes("");
                    setRejectError("");
                  }}
                >
                  Reject
                </Button>
              </Stack>
            </CardContent>
          </Card>
        ))}
      </Stack>

      {/* Reject Dialog */}
      <Dialog
        open={!!rejectTarget}
        onClose={() => setRejectTarget(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Reject Question</DialogTitle>
        <DialogContent>
          {rejectTarget && (
            <Stack spacing={2} sx={{ mt: 1 }}>
              <Alert severity="warning" variant="outlined">
                <Typography variant="body2">
                  {rejectTarget.question_text}
                </Typography>
              </Alert>
              <TextField
                label="Rejection Reason (required)"
                multiline
                minRows={2}
                fullWidth
                value={rejectNotes}
                onChange={(e) => setRejectNotes(e.target.value)}
                placeholder="Explain why this question doesn't meet our standards..."
              />
              {rejectError && <Alert severity="error">{rejectError}</Alert>}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRejectTarget(null)}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleReject}
            disabled={rejectMutation.isPending}
          >
            {rejectMutation.isPending ? "Rejecting..." : "Reject"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
