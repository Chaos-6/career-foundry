/**
 * Full-page loading indicator with optional message.
 *
 * Replaces the repetitive pattern of:
 *   <Box sx={{ textAlign: "center", py: 8 }}>
 *     <CircularProgress />
 *     <Typography>Loading...</Typography>
 *   </Box>
 *
 * Used as the loading state for pages that fetch data on mount.
 */

import React from "react";
import { Box, CircularProgress, Typography } from "@mui/material";

interface PageLoaderProps {
  /** Optional loading message */
  message?: string;
}

export default function PageLoader({ message = "Loading..." }: PageLoaderProps) {
  return (
    <Box sx={{ textAlign: "center", py: 8 }}>
      <CircularProgress size={48} />
      <Typography sx={{ mt: 2 }} color="text.secondary">
        {message}
      </Typography>
    </Box>
  );
}
