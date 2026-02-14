/**
 * Reusable empty state component for pages with no data.
 *
 * Shows an icon, title, description, and an optional CTA button.
 * Consistent look across all pages — reduces boilerplate.
 */

import React, { ReactNode } from "react";
import { Box, Button, Card, CardContent, Typography } from "@mui/material";
import InboxIcon from "@mui/icons-material/Inbox";

interface EmptyStateProps {
  /** Icon displayed at the top. Defaults to InboxIcon if not provided. */
  icon?: ReactNode;
  /** Heading text (e.g. "No Evaluations Yet") */
  title: string;
  /** Descriptive text explaining what to do */
  description?: string;
  /** Label for the action button */
  actionLabel?: string;
  /** Click handler for the action button */
  onAction?: () => void;
}

export default function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <Card>
      <CardContent sx={{ textAlign: "center", py: 6, px: 3 }}>
        <Box sx={{ mb: 2, color: "text.secondary" }}>
          {icon || <InboxIcon sx={{ fontSize: 56, opacity: 0.5 }} />}
        </Box>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          {title}
        </Typography>
        {description && (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mb: actionLabel ? 3 : 0, maxWidth: 400, mx: "auto" }}
          >
            {description}
          </Typography>
        )}
        {actionLabel && onAction && (
          <Button variant="contained" onClick={onAction}>
            {actionLabel}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
