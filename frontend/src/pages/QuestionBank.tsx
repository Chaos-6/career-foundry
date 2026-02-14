/**
 * Question Bank page — browse, filter, and search behavioral questions.
 *
 * Features:
 * - Filter by role, difficulty, competency via dropdowns
 * - Full-text search across question text
 * - Each card shows role tags, competency tags, difficulty badge
 * - "Practice" button → New Evaluation with question pre-selected
 * - "Mock Interview" button → starts a timed session
 * - "AI Generator" button → starts answer generation flow
 * - "Submit Question" — authenticated users can submit community questions
 * - Pagination with "Load More"
 */

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Skeleton,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import RateReviewIcon from "@mui/icons-material/RateReview";
import TimerIcon from "@mui/icons-material/Timer";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import ShuffleIcon from "@mui/icons-material/Shuffle";
import ClearIcon from "@mui/icons-material/Clear";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import PeopleIcon from "@mui/icons-material/People";

import { listQuestions, getRandomQuestion, submitQuestion, Question } from "../api/client";
import { useAuth } from "../hooks/useAuth";

const ROLES = ["MLE", "PM", "TPM", "EM"];
const DIFFICULTIES = ["standard", "advanced", "senior_plus"];
const LEVEL_BANDS = [
  { value: "entry", label: "Entry (L3-L4)" },
  { value: "mid", label: "Mid (L4-L5)" },
  { value: "senior", label: "Senior (L5-L6)" },
  { value: "staff", label: "Staff+ (L6-L7)" },
  { value: "manager", label: "Manager" },
];

const COMPETENCIES = [
  "leadership",
  "teamwork",
  "conflict_resolution",
  "technical_challenge",
  "problem_solving",
  "failure_resilience",
  "innovation",
  "communication",
  "customer_obsession",
  "ownership",
  "decision_making",
  "adaptability",
  "mentorship",
];

const difficultyColors: Record<string, "default" | "warning" | "error"> = {
  standard: "default",
  advanced: "warning",
  senior_plus: "error",
};

export default function QuestionBank() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();

  // Filter state
  const [role, setRole] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [levelBand, setLevelBand] = useState("");
  const [competency, setCompetency] = useState("");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  // Submit question dialog state
  const [submitOpen, setSubmitOpen] = useState(false);
  const [submitText, setSubmitText] = useState("");
  const [submitRoles, setSubmitRoles] = useState<string[]>([]);
  const [submitCompetencies, setSubmitCompetencies] = useState<string[]>([]);
  const [submitDifficulty, setSubmitDifficulty] = useState("standard");
  const [submitLevel, setSubmitLevel] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["questions", role, difficulty, levelBand, competency, search],
    queryFn: () =>
      listQuestions({
        role: role || undefined,
        difficulty: difficulty || undefined,
        level: levelBand || undefined,
        competency: competency || undefined,
        search: search || undefined,
        limit: 200,
      }),
  });

  const hasFilters = role || difficulty || levelBand || competency || search;

  // Submit question mutation
  const submitMutation = useMutation({
    mutationFn: () =>
      submitQuestion({
        question_text: submitText,
        role_tags: submitRoles,
        competency_tags: submitCompetencies,
        difficulty: submitDifficulty,
        level_band: submitLevel || undefined,
      }),
    onSuccess: () => {
      setSubmitSuccess(true);
      setSubmitText("");
      setSubmitRoles([]);
      setSubmitCompetencies([]);
      setSubmitDifficulty("standard");
      setSubmitLevel("");
      setSubmitError("");
      // Refresh question list in case it got approved immediately (won't show yet, but fresh data)
      queryClient.invalidateQueries({ queryKey: ["questions"] });
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      setSubmitError(
        typeof detail === "string"
          ? detail
          : "Failed to submit question. Please try again."
      );
    },
  });

  const handleSubmitQuestion = () => {
    setSubmitError("");
    if (submitText.trim().length < 20) {
      setSubmitError("Question must be at least 20 characters.");
      return;
    }
    submitMutation.mutate();
  };

  const handleCloseSubmit = () => {
    setSubmitOpen(false);
    setSubmitSuccess(false);
    setSubmitError("");
  };

  const handleClearFilters = () => {
    setRole("");
    setDifficulty("");
    setLevelBand("");
    setCompetency("");
    setSearch("");
    setSearchInput("");
  };

  const handleSearch = () => {
    setSearch(searchInput);
  };

  const handleRandomQuestion = async () => {
    try {
      const q = await getRandomQuestion({
        role: role || undefined,
        difficulty: difficulty || undefined,
        level: levelBand || undefined,
      });
      navigate("/evaluate", {
        state: { questionId: q.id, questionText: q.question_text },
      });
    } catch {
      // If no match, just navigate to evaluate
      navigate("/evaluate");
    }
  };

  return (
    <Box sx={{ maxWidth: 900, mx: "auto" }}>
      {/* Header */}
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        sx={{ mb: 3 }}
        spacing={1}
      >
        <Box>
          <Typography
            variant="h4"
            gutterBottom
            sx={{ fontSize: { xs: "1.5rem", sm: "2.125rem" } }}
          >
            Question Bank
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {isLoading
              ? "Loading..."
              : data
              ? `${data.total} question${data.total !== 1 ? "s" : ""} available`
              : "Browse questions"}
          </Typography>
        </Box>
        <Stack direction="row" spacing={1}>
          {isAuthenticated && (
            <Button
              variant="contained"
              color="secondary"
              startIcon={<AddCircleOutlineIcon />}
              onClick={() => {
                setSubmitSuccess(false);
                setSubmitOpen(true);
              }}
            >
              Submit Question
            </Button>
          )}
          <Button
            variant="outlined"
            startIcon={<ShuffleIcon />}
            onClick={handleRandomQuestion}
          >
            Random Question
          </Button>
        </Stack>
      </Stack>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack spacing={2}>
            {/* Row 1: Dropdowns */}
            <Stack
              direction={{ xs: "column", sm: "row" }}
              spacing={2}
            >
              <FormControl sx={{ minWidth: 120 }} size="small">
                <InputLabel>Role</InputLabel>
                <Select
                  value={role}
                  label="Role"
                  onChange={(e) => setRole(e.target.value)}
                >
                  <MenuItem value="">All Roles</MenuItem>
                  {ROLES.map((r) => (
                    <MenuItem key={r} value={r}>
                      {r}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl sx={{ minWidth: 140 }} size="small">
                <InputLabel>Difficulty</InputLabel>
                <Select
                  value={difficulty}
                  label="Difficulty"
                  onChange={(e) => setDifficulty(e.target.value)}
                >
                  <MenuItem value="">All Levels</MenuItem>
                  {DIFFICULTIES.map((d) => (
                    <MenuItem key={d} value={d}>
                      {d.replace("_", " ")}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl sx={{ minWidth: 160 }} size="small">
                <InputLabel>Level Band</InputLabel>
                <Select
                  value={levelBand}
                  label="Level Band"
                  onChange={(e) => setLevelBand(e.target.value)}
                >
                  <MenuItem value="">All Levels</MenuItem>
                  {LEVEL_BANDS.map((lb) => (
                    <MenuItem key={lb.value} value={lb.value}>
                      {lb.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl sx={{ minWidth: 180 }} size="small">
                <InputLabel>Competency</InputLabel>
                <Select
                  value={competency}
                  label="Competency"
                  onChange={(e) => setCompetency(e.target.value)}
                >
                  <MenuItem value="">All Competencies</MenuItem>
                  {COMPETENCIES.map((c) => (
                    <MenuItem key={c} value={c}>
                      {c.replace(/_/g, " ")}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Stack>

            {/* Row 2: Search */}
            <Stack direction="row" spacing={1}>
              <TextField
                label="Search questions"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSearch();
                }}
                size="small"
                sx={{ flexGrow: 1 }}
                placeholder="e.g. conflict, leadership, deadline..."
              />
              <Button
                variant="contained"
                onClick={handleSearch}
                startIcon={<SearchIcon />}
              >
                Search
              </Button>
              {hasFilters && (
                <Button
                  variant="text"
                  onClick={handleClearFilters}
                  startIcon={<ClearIcon />}
                  color="inherit"
                >
                  Clear
                </Button>
              )}
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      {/* Error state */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load questions. Please try again.
        </Alert>
      )}

      {/* Loading state */}
      {isLoading && (
        <Stack spacing={2}>
          {[1, 2, 3, 4, 5].map((i) => (
            <Card key={i}>
              <CardContent>
                <Skeleton variant="text" width="80%" height={24} />
                <Skeleton variant="text" width="40%" height={20} sx={{ mt: 1 }} />
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}

      {/* Empty state */}
      {!isLoading && data?.items.length === 0 && (
        <Card>
          <CardContent sx={{ textAlign: "center", py: 6 }}>
            <SearchIcon sx={{ fontSize: 48, color: "text.disabled", mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              No questions found
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Try adjusting your filters or search terms.
            </Typography>
            <Button variant="outlined" onClick={handleClearFilters}>
              Clear All Filters
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Question list */}
      {!isLoading && data && data.items.length > 0 && (
        <Grid container spacing={2}>
          {data.items.map((q: Question) => (
            <Grid item xs={12} key={q.id}>
              <Card
                sx={{
                  "&:hover": { boxShadow: 3 },
                  transition: "box-shadow 0.2s",
                }}
              >
                <CardContent>
                  <Typography variant="body1" sx={{ mb: 1.5 }}>
                    {q.question_text}
                  </Typography>

                  {/* Tags row */}
                  <Stack
                    direction="row"
                    spacing={0.5}
                    flexWrap="wrap"
                    useFlexGap
                    sx={{ mb: 1.5 }}
                  >
                    {q.role_tags.map((t) => (
                      <Chip
                        key={`role-${t}`}
                        label={t}
                        size="small"
                        color="primary"
                        variant="outlined"
                        onClick={() => setRole(t)}
                      />
                    ))}
                    {q.competency_tags.map((t) => (
                      <Chip
                        key={`comp-${t}`}
                        label={t.replace(/_/g, " ")}
                        size="small"
                        variant="outlined"
                        onClick={() => setCompetency(t)}
                      />
                    ))}
                    <Chip
                      label={q.difficulty.replace("_", " ")}
                      size="small"
                      color={difficultyColors[q.difficulty] || "default"}
                    />
                    {q.level_band && (
                      <Chip
                        label={
                          LEVEL_BANDS.find((lb) => lb.value === q.level_band)
                            ?.label || q.level_band
                        }
                        size="small"
                        color="info"
                        variant="outlined"
                        onClick={() => setLevelBand(q.level_band!)}
                      />
                    )}
                    {q.source === "community" && (
                      <Chip
                        icon={<PeopleIcon />}
                        label="Community"
                        size="small"
                        color="secondary"
                        variant="outlined"
                      />
                    )}
                  </Stack>

                  {/* Action buttons */}
                  <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                    <Tooltip title="Evaluate an answer for this question">
                      <Button
                        size="small"
                        variant="contained"
                        startIcon={<RateReviewIcon />}
                        onClick={() =>
                          navigate("/evaluate", {
                            state: { questionId: q.id, questionText: q.question_text },
                          })
                        }
                      >
                        Practice
                      </Button>
                    </Tooltip>
                    <Tooltip title="Timed mock interview with this question">
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<TimerIcon />}
                        onClick={() =>
                          navigate("/mock", {
                            state: { questionId: q.id, questionText: q.question_text },
                          })
                        }
                      >
                        Mock
                      </Button>
                    </Tooltip>
                    <Tooltip title="Generate an answer using AI">
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<AutoAwesomeIcon />}
                        onClick={() =>
                          navigate("/generator", {
                            state: { questionId: q.id, questionText: q.question_text },
                          })
                        }
                      >
                        AI Draft
                      </Button>
                    </Tooltip>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Results count footer */}
      {!isLoading && data && data.items.length > 0 && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mt: 2, textAlign: "center" }}
        >
          Showing {data.items.length} of {data.total} questions
        </Typography>
      )}

      {/* Submit Question Dialog */}
      <Dialog
        open={submitOpen}
        onClose={handleCloseSubmit}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Stack direction="row" alignItems="center" spacing={1}>
            <PeopleIcon color="secondary" />
            <span>Submit a Community Question</span>
          </Stack>
        </DialogTitle>
        <DialogContent>
          {submitSuccess ? (
            <Alert severity="success" sx={{ mt: 1 }}>
              Question submitted! It will appear in the bank once a moderator
              approves it. Thank you for contributing!
            </Alert>
          ) : (
            <Stack spacing={2} sx={{ mt: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Help grow the question bank! Submit a behavioral interview
                question and it will be reviewed by a moderator before going
                live.
              </Typography>

              <TextField
                label="Question Text"
                multiline
                minRows={3}
                fullWidth
                value={submitText}
                onChange={(e) => setSubmitText(e.target.value)}
                placeholder="Tell me about a time when you..."
                helperText={`${submitText.length}/500 characters (min 20)`}
                inputProps={{ maxLength: 500 }}
              />

              <Autocomplete
                multiple
                options={ROLES}
                value={submitRoles}
                onChange={(_, v) => setSubmitRoles(v)}
                renderInput={(params) => (
                  <TextField {...params} label="Role Tags (optional)" size="small" />
                )}
                size="small"
              />

              <Autocomplete
                multiple
                options={COMPETENCIES}
                getOptionLabel={(o) => o.replace(/_/g, " ")}
                value={submitCompetencies}
                onChange={(_, v) => setSubmitCompetencies(v)}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Competency Tags (optional)"
                    size="small"
                  />
                )}
                size="small"
              />

              <Stack direction="row" spacing={2}>
                <FormControl size="small" sx={{ minWidth: 140 }}>
                  <InputLabel>Difficulty</InputLabel>
                  <Select
                    value={submitDifficulty}
                    label="Difficulty"
                    onChange={(e) => setSubmitDifficulty(e.target.value)}
                  >
                    {DIFFICULTIES.map((d) => (
                      <MenuItem key={d} value={d}>
                        {d.replace("_", " ")}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <FormControl size="small" sx={{ minWidth: 160 }}>
                  <InputLabel>Level Band (optional)</InputLabel>
                  <Select
                    value={submitLevel}
                    label="Level Band (optional)"
                    onChange={(e) => setSubmitLevel(e.target.value)}
                  >
                    <MenuItem value="">None</MenuItem>
                    {LEVEL_BANDS.map((lb) => (
                      <MenuItem key={lb.value} value={lb.value}>
                        {lb.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Stack>

              {submitError && (
                <Alert severity="error">{submitError}</Alert>
              )}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseSubmit}>
            {submitSuccess ? "Close" : "Cancel"}
          </Button>
          {!submitSuccess && (
            <Button
              variant="contained"
              onClick={handleSubmitQuestion}
              disabled={submitMutation.isPending}
            >
              {submitMutation.isPending ? "Submitting..." : "Submit for Review"}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
}
