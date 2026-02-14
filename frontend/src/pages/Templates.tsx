/**
 * Answer Templates page — manage reusable STAR answer frameworks.
 *
 * Features:
 * - List all saved templates with tag chips and usage stats
 * - Create new templates with the inline editor
 * - Edit existing templates
 * - Delete templates with confirmation
 * - Pin a default template (auto-loaded in NewEvaluation)
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
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Divider,
  IconButton,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import CloseIcon from "@mui/icons-material/Close";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import PushPinIcon from "@mui/icons-material/PushPin";
import PushPinOutlinedIcon from "@mui/icons-material/PushPinOutlined";
import SaveIcon from "@mui/icons-material/Save";

import {
  listTemplates,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  AnswerTemplate,
} from "../api/client";
import EmptyState from "../components/EmptyState";
import PageLoader from "../components/PageLoader";

const ROLE_OPTIONS = ["MLE", "PM", "TPM", "EM"];
const COMPETENCY_OPTIONS = [
  "leadership",
  "conflict",
  "teamwork",
  "technical_challenge",
  "failure",
  "initiative",
  "communication",
  "customer_focus",
];

export default function Templates() {
  const queryClient = useQueryClient();

  // Editor state
  const [editing, setEditing] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [templateText, setTemplateText] = useState("");
  const [roleTags, setRoleTags] = useState<string[]>([]);
  const [competencyTags, setCompetencyTags] = useState<string[]>([]);
  const [error, setError] = useState("");

  // Delete confirmation dialog
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  // Fetch templates
  const {
    data: templates = [],
    isLoading,
    error: fetchError,
  } = useQuery({
    queryKey: ["templates"],
    queryFn: listTemplates,
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: createTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      resetEditor();
    },
    onError: (err: any) => {
      setError(
        err.response?.data?.detail || "Failed to create template."
      );
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) =>
      updateTemplate(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      resetEditor();
    },
    onError: (err: any) => {
      setError(
        err.response?.data?.detail || "Failed to update template."
      );
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      setDeleteDialogOpen(false);
      setDeleteTargetId(null);
    },
  });

  // Toggle default mutation
  const toggleDefaultMutation = useMutation({
    mutationFn: ({ id, isDefault }: { id: string; isDefault: boolean }) =>
      updateTemplate(id, { is_default: isDefault }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
    },
  });

  const resetEditor = () => {
    setEditing(false);
    setEditingId(null);
    setName("");
    setTemplateText("");
    setRoleTags([]);
    setCompetencyTags([]);
    setError("");
  };

  const handleStartCreate = () => {
    resetEditor();
    setEditing(true);
  };

  const handleStartEdit = (template: AnswerTemplate) => {
    setEditingId(template.id);
    setName(template.name);
    setTemplateText(template.template_text);
    setRoleTags(template.role_tags || []);
    setCompetencyTags(template.competency_tags || []);
    setError("");
    setEditing(true);
  };

  const handleSave = () => {
    setError("");
    if (!name.trim()) return setError("Template name is required.");
    if (templateText.trim().split(/\s+/).length < 5)
      return setError("Template text must be at least 5 words.");

    const payload = {
      name: name.trim(),
      template_text: templateText.trim(),
      role_tags: roleTags,
      competency_tags: competencyTags,
    };

    if (editingId) {
      updateMutation.mutate({ id: editingId, payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const toggleTag = (
    tag: string,
    current: string[],
    setter: (v: string[]) => void
  ) => {
    if (current.includes(tag)) {
      setter(current.filter((t) => t !== tag));
    } else {
      setter([...current, tag]);
    }
  };

  const saving = createMutation.isPending || updateMutation.isPending;

  if (isLoading) return <PageLoader message="Loading templates..." />;

  if (fetchError) {
    return (
      <Alert severity="error">
        Failed to load templates. Please try again.
      </Alert>
    );
  }

  return (
    <Box sx={{ maxWidth: 800, mx: "auto" }}>
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 3 }}
      >
        <Box>
          <Typography
            variant="h4"
            gutterBottom
            sx={{ fontSize: { xs: "1.5rem", sm: "2.125rem" } }}
          >
            Answer Templates
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Save and reuse STAR answer frameworks for common scenarios.
          </Typography>
        </Box>
        {!editing && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleStartCreate}
          >
            New Template
          </Button>
        )}
      </Stack>

      {/* Editor — create or edit */}
      <Collapse in={editing}>
        <Card
          sx={{
            mb: 3,
            border: 2,
            borderColor: "primary.main",
          }}
        >
          <CardContent>
            <Stack
              direction="row"
              justifyContent="space-between"
              alignItems="center"
              sx={{ mb: 2 }}
            >
              <Typography variant="h6">
                {editingId ? "Edit Template" : "New Template"}
              </Typography>
              <IconButton size="small" onClick={resetEditor}>
                <CloseIcon />
              </IconButton>
            </Stack>

            <Stack spacing={2}>
              <TextField
                fullWidth
                label="Template Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Leadership Challenge — Amazon LP"
                size="small"
              />

              <TextField
                fullWidth
                multiline
                minRows={6}
                maxRows={16}
                label="Template Text"
                value={templateText}
                onChange={(e) => setTemplateText(e.target.value)}
                placeholder={
                  "Situation: [Describe the context — what team, project, timeline...]\n\n" +
                  "Task: [What was your specific responsibility?]\n\n" +
                  "Action: [What did YOU do? Be specific about your steps...]\n\n" +
                  "Result: [Quantify the outcome — metrics, impact, learnings...]"
                }
              />

              {/* Role tags */}
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Role Tags (optional)
                </Typography>
                <Stack direction="row" spacing={0.5} flexWrap="wrap" sx={{ mt: 0.5 }}>
                  {ROLE_OPTIONS.map((r) => (
                    <Chip
                      key={r}
                      label={r}
                      size="small"
                      variant={roleTags.includes(r) ? "filled" : "outlined"}
                      color={roleTags.includes(r) ? "primary" : "default"}
                      onClick={() => toggleTag(r, roleTags, setRoleTags)}
                    />
                  ))}
                </Stack>
              </Box>

              {/* Competency tags */}
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Competency Tags (optional)
                </Typography>
                <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap sx={{ mt: 0.5 }}>
                  {COMPETENCY_OPTIONS.map((c) => (
                    <Chip
                      key={c}
                      label={c.replace(/_/g, " ")}
                      size="small"
                      variant={competencyTags.includes(c) ? "filled" : "outlined"}
                      color={competencyTags.includes(c) ? "secondary" : "default"}
                      onClick={() =>
                        toggleTag(c, competencyTags, setCompetencyTags)
                      }
                    />
                  ))}
                </Stack>
              </Box>

              {error && (
                <Alert severity="error" onClose={() => setError("")}>
                  {error}
                </Alert>
              )}

              <Stack direction="row" spacing={1} justifyContent="flex-end">
                <Button variant="outlined" onClick={resetEditor}>
                  Cancel
                </Button>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? "Saving..." : editingId ? "Update" : "Save Template"}
                </Button>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Collapse>

      {/* Template list */}
      {templates.length === 0 && !editing ? (
        <EmptyState
          title="No templates yet"
          description="Create reusable STAR answer frameworks to speed up your evaluation workflow. You can also save templates from evaluated answers."
          actionLabel="Create Your First Template"
          onAction={handleStartCreate}
        />
      ) : (
        <Stack spacing={2}>
          {templates.map((template) => (
            <Card key={template.id}>
              <CardContent>
                <Stack
                  direction="row"
                  justifyContent="space-between"
                  alignItems="flex-start"
                >
                  <Box sx={{ flex: 1, mr: 2 }}>
                    <Stack direction="row" alignItems="center" spacing={1}>
                      <Typography variant="h6" sx={{ fontSize: "1.1rem" }}>
                        {template.name}
                      </Typography>
                      {template.is_default && (
                        <Chip
                          label="Default"
                          size="small"
                          color="primary"
                          variant="outlined"
                          icon={<PushPinIcon sx={{ fontSize: 14 }} />}
                        />
                      )}
                    </Stack>

                    {/* Tags */}
                    <Stack
                      direction="row"
                      spacing={0.5}
                      flexWrap="wrap"
                      useFlexGap
                      sx={{ mt: 1 }}
                    >
                      {template.role_tags?.map((t) => (
                        <Chip key={t} label={t} size="small" variant="outlined" />
                      ))}
                      {template.competency_tags?.map((t) => (
                        <Chip
                          key={t}
                          label={t.replace(/_/g, " ")}
                          size="small"
                          color="secondary"
                          variant="outlined"
                        />
                      ))}
                    </Stack>

                    {/* Preview */}
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{
                        mt: 1.5,
                        whiteSpace: "pre-wrap",
                        maxHeight: 120,
                        overflow: "hidden",
                        position: "relative",
                        "&::after": {
                          content: '""',
                          position: "absolute",
                          bottom: 0,
                          left: 0,
                          right: 0,
                          height: 40,
                          background:
                            "linear-gradient(transparent, white)",
                        },
                      }}
                    >
                      {template.template_text}
                    </Typography>

                    {/* Stats */}
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ mt: 1, display: "block" }}
                    >
                      Used {template.usage_count} time
                      {template.usage_count !== 1 ? "s" : ""} · Created{" "}
                      {new Date(template.created_at).toLocaleDateString()}
                    </Typography>
                  </Box>

                  {/* Actions */}
                  <Stack direction="column" spacing={0.5}>
                    <Tooltip
                      title={
                        template.is_default
                          ? "Unpin as default"
                          : "Pin as default"
                      }
                    >
                      <IconButton
                        size="small"
                        color={template.is_default ? "primary" : "default"}
                        onClick={() =>
                          toggleDefaultMutation.mutate({
                            id: template.id,
                            isDefault: !template.is_default,
                          })
                        }
                      >
                        {template.is_default ? (
                          <PushPinIcon />
                        ) : (
                          <PushPinOutlinedIcon />
                        )}
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit">
                      <IconButton
                        size="small"
                        onClick={() => handleStartEdit(template)}
                      >
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => {
                          setDeleteTargetId(template.id);
                          setDeleteDialogOpen(true);
                        }}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}

      {/* Delete confirmation dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Template?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            This template will be permanently deleted. This action cannot be
            undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            color="error"
            variant="contained"
            onClick={() => {
              if (deleteTargetId) {
                deleteMutation.mutate(deleteTargetId);
              }
            }}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? "Deleting..." : "Delete"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
