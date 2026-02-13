/**
 * Error Boundary component.
 *
 * Catches unhandled React rendering errors and displays a friendly
 * fallback UI instead of a white screen. Class component because
 * React error boundaries must use componentDidCatch (no hooks equivalent).
 */

import React, { Component, ErrorInfo, ReactNode } from "react";
import { Box, Button, Card, CardContent, Typography } from "@mui/material";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            minHeight: "50vh",
            p: 3,
          }}
        >
          <Card sx={{ maxWidth: 500, textAlign: "center" }}>
            <CardContent sx={{ py: 4 }}>
              <ErrorOutlineIcon
                sx={{ fontSize: 64, color: "error.main", mb: 2 }}
              />
              <Typography variant="h5" gutterBottom>
                Something went wrong
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mb: 3 }}
              >
                An unexpected error occurred. Please try refreshing the page.
              </Typography>
              {this.state.error && (
                <Typography
                  variant="caption"
                  color="text.disabled"
                  component="pre"
                  sx={{
                    textAlign: "left",
                    bgcolor: "grey.100",
                    p: 1.5,
                    borderRadius: 1,
                    overflow: "auto",
                    mb: 2,
                    maxHeight: 100,
                  }}
                >
                  {this.state.error.message}
                </Typography>
              )}
              <Button
                variant="contained"
                onClick={() => window.location.reload()}
              >
                Refresh Page
              </Button>
            </CardContent>
          </Card>
        </Box>
      );
    }

    return this.props.children;
  }
}
