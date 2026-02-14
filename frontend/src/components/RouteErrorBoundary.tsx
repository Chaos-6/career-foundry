/**
 * Route-level Error Boundary — catches rendering errors within a page
 * while keeping the Layout (sidebar + header) intact.
 *
 * Differs from the top-level ErrorBoundary in index.tsx:
 * - Shows error inside the content area, not full-screen
 * - Offers "Go to Dashboard" navigation instead of hard refresh
 * - Automatically resets when the user navigates to a different route
 *
 * The key prop trick: React Router's <Outlet /> doesn't change the
 * component tree when the path changes, so the error boundary won't
 * reset on its own. We pass `location.pathname` as the `resetKey`
 * prop so the boundary resets when the route changes.
 */

import React, { Component, ErrorInfo, ReactNode } from "react";
import { Alert, Box, Button, Card, CardContent, Stack, Typography } from "@mui/material";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import HomeIcon from "@mui/icons-material/Home";
import RefreshIcon from "@mui/icons-material/Refresh";

interface Props {
  children: ReactNode;
  /** When this key changes, the boundary resets its error state. */
  resetKey?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class RouteErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log for debugging — in production you'd send this to Sentry/etc.
    console.error("[RouteErrorBoundary]", error, errorInfo);
  }

  componentDidUpdate(prevProps: Props) {
    // Reset error state when the route changes
    if (this.state.hasError && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ hasError: false, error: null });
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box sx={{ maxWidth: 600, mx: "auto", py: 4 }}>
          <Card>
            <CardContent sx={{ textAlign: "center", py: 4 }}>
              <ErrorOutlineIcon
                sx={{ fontSize: 56, color: "error.main", mb: 2 }}
              />
              <Typography variant="h5" gutterBottom>
                This page encountered an error
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mb: 2 }}
              >
                Something went wrong rendering this page. You can try refreshing
                or navigate to another section using the sidebar.
              </Typography>

              {this.state.error && (
                <Alert
                  severity="error"
                  sx={{
                    textAlign: "left",
                    mb: 3,
                    mx: "auto",
                    maxWidth: 480,
                  }}
                >
                  <Typography
                    variant="caption"
                    component="pre"
                    sx={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}
                  >
                    {this.state.error.message}
                  </Typography>
                </Alert>
              )}

              <Stack
                direction="row"
                spacing={2}
                justifyContent="center"
              >
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={() =>
                    this.setState({ hasError: false, error: null })
                  }
                >
                  Try Again
                </Button>
                <Button
                  variant="contained"
                  startIcon={<HomeIcon />}
                  href="/"
                >
                  Go to Dashboard
                </Button>
              </Stack>
            </CardContent>
          </Card>
        </Box>
      );
    }

    return this.props.children;
  }
}
