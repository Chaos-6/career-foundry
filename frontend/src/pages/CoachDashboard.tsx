/**
 * Coach Dashboard — manage students, view progress, and add feedback.
 *
 * Three sections:
 * 1. Invite form — send coaching invites by email
 * 2. Student roster — cards with stats (evals, avg score, last active)
 * 3. Student detail — click a student to see their evaluation history
 *    and add coach notes to individual evaluations
 *
 * Also serves as the student's coaching view — shows pending invites
 * and active coaches at the bottom.
 */

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Grid,
  IconButton,
  LinearProgress,
  Skeleton,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import GroupsIcon from "@mui/icons-material/Groups";
import PersonAddIcon from "@mui/icons-material/PersonAdd";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import SchoolIcon from "@mui/icons-material/School";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CancelIcon from "@mui/icons-material/Cancel";
import EditNoteIcon from "@mui/icons-material/EditNote";
import RemoveCircleOutlineIcon from "@mui/icons-material/RemoveCircleOutline";

import {
  inviteStudent,
  getCoachStudents,
  getStudentEvaluations,
  updateCoachNotes,
  getMyInvites,
  getMyCoaches,
  acceptInvite,
  declineInvite,
  removeRelationship,
  StudentSummary,
  StudentEvaluation,
  CoachingRelationship,
} from "../api/client";
import { useAuth } from "../hooks/useAuth";

// ---------------------------------------------------------------------------
// Score color helper
// ---------------------------------------------------------------------------

function scoreColor(score: number | null): string {
  if (!score) return "text.secondary";
  if (score >= 4) return "success.main";
  if (score >= 3) return "warning.main";
  return "error.main";
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export default function CoachDashboard() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  // Invite form state
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteError, setInviteError] = useState("");
  const [inviteSuccess, setInviteSuccess] = useState("");

  // Student detail state
  const [selectedStudent, setSelectedStudent] = useState<StudentSummary | null>(null);

  // Coach notes dialog
  const [notesTarget, setNotesTarget] = useState<StudentEvaluation | null>(null);
  const [notesText, setNotesText] = useState("");
  const [notesFocusAreas, setNotesFocusAreas] = useState("");
  const [notesError, setNotesError] = useState("");

  // ---------------------------------------------------------------------------
  // Queries
  // ---------------------------------------------------------------------------

  const { data: dashboard, isLoading: loadingDashboard } = useQuery({
    queryKey: ["coach-students"],
    queryFn: getCoachStudents,
  });

  const { data: invites = [], isLoading: loadingInvites } = useQuery({
    queryKey: ["my-invites"],
    queryFn: getMyInvites,
  });

  const { data: coaches = [] } = useQuery({
    queryKey: ["my-coaches"],
    queryFn: getMyCoaches,
  });

  const { data: studentEvals, isLoading: loadingEvals } = useQuery({
    queryKey: ["student-evals", selectedStudent?.student_id],
    queryFn: () => getStudentEvaluations(selectedStudent!.student_id),
    enabled: !!selectedStudent,
  });

  // ---------------------------------------------------------------------------
  // Mutations
  // ---------------------------------------------------------------------------

  const inviteMutation = useMutation({
    mutationFn: () => inviteStudent(inviteEmail),
    onSuccess: () => {
      setInviteSuccess(`Invite sent to ${inviteEmail}!`);
      setInviteEmail("");
      setInviteError("");
      queryClient.invalidateQueries({ queryKey: ["coach-students"] });
    },
    onError: (err: any) => {
      setInviteError(err.response?.data?.detail || "Failed to send invite.");
    },
  });

  const acceptMutation = useMutation({
    mutationFn: (id: string) => acceptInvite(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-invites"] });
      queryClient.invalidateQueries({ queryKey: ["my-coaches"] });
    },
  });

  const declineMutation = useMutation({
    mutationFn: (id: string) => declineInvite(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-invites"] });
    },
  });

  const removeMutation = useMutation({
    mutationFn: (id: string) => removeRelationship(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["coach-students"] });
      queryClient.invalidateQueries({ queryKey: ["my-coaches"] });
    },
  });

  const notesMutation = useMutation({
    mutationFn: () => {
      if (!notesTarget) throw new Error("No target");
      return updateCoachNotes(notesTarget.evaluation_id, {
        notes: notesText,
        focus_areas: notesFocusAreas
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      });
    },
    onSuccess: () => {
      setNotesTarget(null);
      setNotesText("");
      setNotesFocusAreas("");
      setNotesError("");
      // Refresh student evaluations to show updated notes
      if (selectedStudent) {
        queryClient.invalidateQueries({
          queryKey: ["student-evals", selectedStudent.student_id],
        });
      }
    },
    onError: (err: any) => {
      setNotesError(err.response?.data?.detail || "Failed to save notes.");
    },
  });

  const handleInvite = () => {
    setInviteError("");
    setInviteSuccess("");
    if (!inviteEmail.includes("@")) {
      setInviteError("Please enter a valid email address.");
      return;
    }
    inviteMutation.mutate();
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <Box sx={{ maxWidth: 900, mx: "auto" }}>
      {/* Header */}
      <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 1 }}>
        <GroupsIcon color="primary" fontSize="large" />
        <Typography
          variant="h4"
          sx={{ fontSize: { xs: "1.5rem", sm: "2.125rem" } }}
        >
          Coaching
        </Typography>
      </Stack>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Invite students, track their progress, and provide personalized feedback
        on their evaluations.
      </Typography>

      {/* ── Pending Invites (for students) ─────────────────────────── */}
      {invites.length > 0 && (
        <Card sx={{ mb: 3, border: "2px solid", borderColor: "warning.main" }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <SchoolIcon sx={{ mr: 1, verticalAlign: "middle" }} />
              Pending Coaching Invites
            </Typography>
            <Stack spacing={1}>
              {invites.map((inv) => (
                <Stack
                  key={inv.id}
                  direction="row"
                  alignItems="center"
                  justifyContent="space-between"
                  sx={{ p: 1, bgcolor: "action.hover", borderRadius: 1 }}
                >
                  <Box>
                    <Typography variant="body2" fontWeight={500}>
                      {inv.coach_name || inv.coach_email} wants to coach you
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {inv.coach_email}
                    </Typography>
                  </Box>
                  <Stack direction="row" spacing={1}>
                    <Button
                      size="small"
                      variant="contained"
                      color="success"
                      startIcon={<CheckCircleIcon />}
                      onClick={() => acceptMutation.mutate(inv.id)}
                      disabled={acceptMutation.isPending}
                    >
                      Accept
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      color="error"
                      startIcon={<CancelIcon />}
                      onClick={() => declineMutation.mutate(inv.id)}
                      disabled={declineMutation.isPending}
                    >
                      Decline
                    </Button>
                  </Stack>
                </Stack>
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}

      {/* ── Invite Student ────────────────────────────────────────── */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <PersonAddIcon sx={{ mr: 1, verticalAlign: "middle" }} />
            Invite a Student
          </Typography>
          <Stack direction="row" spacing={1}>
            <TextField
              label="Student's email"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleInvite();
              }}
              size="small"
              sx={{ flexGrow: 1 }}
              placeholder="student@example.com"
            />
            <Button
              variant="contained"
              onClick={handleInvite}
              disabled={inviteMutation.isPending}
            >
              {inviteMutation.isPending ? "Sending..." : "Send Invite"}
            </Button>
          </Stack>
          {inviteError && (
            <Alert severity="error" sx={{ mt: 1 }}>
              {inviteError}
            </Alert>
          )}
          {inviteSuccess && (
            <Alert severity="success" sx={{ mt: 1 }}>
              {inviteSuccess}
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* ── Student Roster ────────────────────────────────────────── */}
      <Typography variant="h6" sx={{ mb: 2 }}>
        Your Students
        {dashboard && (
          <Chip
            label={`${dashboard.total_students} active`}
            size="small"
            color="primary"
            sx={{ ml: 1 }}
          />
        )}
        {dashboard && dashboard.pending_invites > 0 && (
          <Chip
            label={`${dashboard.pending_invites} pending`}
            size="small"
            color="warning"
            sx={{ ml: 0.5 }}
          />
        )}
      </Typography>

      {loadingDashboard && (
        <Stack spacing={2}>
          {[1, 2].map((i) => (
            <Card key={i}>
              <CardContent>
                <Skeleton variant="circular" width={40} height={40} />
                <Skeleton variant="text" width="60%" sx={{ mt: 1 }} />
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}

      {!loadingDashboard && dashboard?.students.length === 0 && (
        <Card>
          <CardContent sx={{ textAlign: "center", py: 4 }}>
            <GroupsIcon sx={{ fontSize: 48, color: "text.disabled", mb: 1 }} />
            <Typography variant="body1" color="text.secondary">
              No active students yet. Send an invite to get started!
            </Typography>
          </CardContent>
        </Card>
      )}

      <Grid container spacing={2} sx={{ mb: 3 }}>
        {dashboard?.students.map((s) => (
          <Grid item xs={12} sm={6} key={s.student_id}>
            <Card
              sx={{
                cursor: "pointer",
                border:
                  selectedStudent?.student_id === s.student_id
                    ? "2px solid"
                    : "1px solid",
                borderColor:
                  selectedStudent?.student_id === s.student_id
                    ? "primary.main"
                    : "divider",
                "&:hover": { boxShadow: 3 },
                transition: "all 0.2s",
              }}
              onClick={() =>
                setSelectedStudent(
                  selectedStudent?.student_id === s.student_id ? null : s
                )
              }
            >
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={1.5}>
                  <Avatar
                    src={s.avatar_url || undefined}
                    sx={{ width: 40, height: 40, bgcolor: "primary.main" }}
                  >
                    {(s.display_name || s.email).charAt(0).toUpperCase()}
                  </Avatar>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="subtitle1" fontWeight={500}>
                      {s.display_name || s.email}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {s.email}
                    </Typography>
                  </Box>
                  <Tooltip title="Remove student">
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        removeMutation.mutate(s.relationship_id);
                      }}
                    >
                      <RemoveCircleOutlineIcon fontSize="small" color="error" />
                    </IconButton>
                  </Tooltip>
                </Stack>

                <Stack
                  direction="row"
                  spacing={2}
                  sx={{ mt: 1.5 }}
                  justifyContent="space-around"
                >
                  <Box sx={{ textAlign: "center" }}>
                    <Typography variant="h6">{s.total_evaluations}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Evals
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: "center" }}>
                    <Typography
                      variant="h6"
                      color={scoreColor(s.average_score)}
                    >
                      {s.average_score?.toFixed(1) || "—"}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Avg Score
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: "center" }}>
                    <Typography
                      variant="h6"
                      color={scoreColor(s.best_score)}
                    >
                      {s.best_score?.toFixed(1) || "—"}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Best
                    </Typography>
                  </Box>
                </Stack>

                {s.latest_evaluation_date && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ mt: 1, display: "block", textAlign: "right" }}
                  >
                    Last active:{" "}
                    {new Date(s.latest_evaluation_date).toLocaleDateString()}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* ── Student Evaluation Detail ─────────────────────────────── */}
      <Collapse in={!!selectedStudent}>
        {selectedStudent && (
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Stack
                direction="row"
                justifyContent="space-between"
                alignItems="center"
              >
                <Typography variant="h6">
                  {selectedStudent.display_name || selectedStudent.email}
                  &apos;s Evaluations
                </Typography>
                <IconButton onClick={() => setSelectedStudent(null)}>
                  <ExpandLessIcon />
                </IconButton>
              </Stack>
              <Divider sx={{ my: 1 }} />

              {loadingEvals && <LinearProgress />}

              {!loadingEvals && studentEvals?.length === 0 && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ py: 2, textAlign: "center" }}
                >
                  No completed evaluations yet.
                </Typography>
              )}

              <Stack spacing={1.5} sx={{ mt: 1 }}>
                {studentEvals?.map((ev) => (
                  <Card
                    key={ev.evaluation_id}
                    variant="outlined"
                    sx={{ bgcolor: "background.default" }}
                  >
                    <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
                      <Stack
                        direction="row"
                        justifyContent="space-between"
                        alignItems="flex-start"
                      >
                        <Box sx={{ flexGrow: 1 }}>
                          <Typography variant="body2" fontWeight={500}>
                            {ev.question_text || "Custom question"}
                          </Typography>
                          <Stack
                            direction="row"
                            spacing={1}
                            sx={{ mt: 0.5 }}
                          >
                            <Chip
                              label={ev.company_name}
                              size="small"
                              variant="outlined"
                            />
                            <Chip
                              label={ev.target_role}
                              size="small"
                              variant="outlined"
                            />
                            <Typography
                              variant="body2"
                              fontWeight={600}
                              color={scoreColor(ev.average_score)}
                            >
                              {ev.average_score?.toFixed(1) || "—"}/5
                            </Typography>
                          </Stack>
                          <Typography
                            variant="caption"
                            color="text.secondary"
                          >
                            {new Date(ev.created_at).toLocaleDateString()} · v
                            {ev.version_number}
                          </Typography>
                        </Box>
                        <Tooltip title="Add/edit coach feedback">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => {
                              setNotesTarget(ev);
                              setNotesText(ev.coach_notes?.notes || "");
                              setNotesFocusAreas(
                                ev.coach_notes?.focus_areas?.join(", ") || ""
                              );
                              setNotesError("");
                            }}
                          >
                            <EditNoteIcon />
                          </IconButton>
                        </Tooltip>
                      </Stack>

                      {/* Show existing coach notes */}
                      {ev.coach_notes && (
                        <Alert
                          severity="info"
                          variant="outlined"
                          sx={{ mt: 1, py: 0.5 }}
                        >
                          <Typography variant="caption" fontWeight={600}>
                            Coach notes:
                          </Typography>
                          <Typography variant="body2">
                            {ev.coach_notes.notes}
                          </Typography>
                          {ev.coach_notes.focus_areas.length > 0 && (
                            <Stack
                              direction="row"
                              spacing={0.5}
                              sx={{ mt: 0.5 }}
                              flexWrap="wrap"
                              useFlexGap
                            >
                              {ev.coach_notes.focus_areas.map((area) => (
                                <Chip
                                  key={area}
                                  label={area}
                                  size="small"
                                  color="info"
                                />
                              ))}
                            </Stack>
                          )}
                        </Alert>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            </CardContent>
          </Card>
        )}
      </Collapse>

      {/* ── My Coaches (student view) ─────────────────────────────── */}
      {coaches.length > 0 && (
        <>
          <Divider sx={{ my: 3 }} />
          <Typography variant="h6" sx={{ mb: 2 }}>
            <SchoolIcon sx={{ mr: 1, verticalAlign: "middle" }} />
            My Coaches
          </Typography>
          <Stack spacing={1}>
            {coaches.map((c) => (
              <Card key={c.id} variant="outlined">
                <CardContent
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    py: 1.5,
                    "&:last-child": { pb: 1.5 },
                  }}
                >
                  <Box>
                    <Typography variant="body1" fontWeight={500}>
                      {c.coach_name || c.coach_email}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {c.coach_email} · Connected{" "}
                      {c.accepted_at
                        ? new Date(c.accepted_at).toLocaleDateString()
                        : ""}
                    </Typography>
                  </Box>
                  <Tooltip title="Remove coach">
                    <IconButton
                      size="small"
                      onClick={() => removeMutation.mutate(c.id)}
                    >
                      <RemoveCircleOutlineIcon fontSize="small" color="error" />
                    </IconButton>
                  </Tooltip>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </>
      )}

      {/* ── Coach Notes Dialog ────────────────────────────────────── */}
      <Dialog
        open={!!notesTarget}
        onClose={() => setNotesTarget(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Coach Feedback</DialogTitle>
        <DialogContent>
          {notesTarget && (
            <Stack spacing={2} sx={{ mt: 1 }}>
              <Alert severity="info" variant="outlined">
                <Typography variant="body2" fontWeight={500}>
                  {notesTarget.question_text || "Custom question"}
                </Typography>
                <Typography variant="caption">
                  Score: {notesTarget.average_score?.toFixed(1) || "—"}/5 ·{" "}
                  {notesTarget.company_name} · {notesTarget.target_role}
                </Typography>
              </Alert>

              <TextField
                label="Your feedback"
                multiline
                minRows={3}
                fullWidth
                value={notesText}
                onChange={(e) => setNotesText(e.target.value)}
                placeholder="Great structure on the Situation — try adding more quantitative detail to the Result section..."
              />

              <TextField
                label="Focus areas (comma-separated)"
                value={notesFocusAreas}
                onChange={(e) => setNotesFocusAreas(e.target.value)}
                size="small"
                placeholder="quantify results, action specificity, time management"
              />

              {notesError && <Alert severity="error">{notesError}</Alert>}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNotesTarget(null)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => notesMutation.mutate()}
            disabled={notesMutation.isPending || !notesText.trim()}
          >
            {notesMutation.isPending ? "Saving..." : "Save Feedback"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
