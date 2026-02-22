/**
 * Entry point — wraps the app with MUI ThemeProvider and React Query.
 *
 * Theme mode (light/dark) is managed by ThemeModeProvider and persisted
 * in localStorage. The ThemedApp component bridges the context to MUI's
 * ThemeProvider via useMemo.
 */

import React, { useMemo } from "react";
import ReactDOM from "react-dom/client";
import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import App from "./App";
import ErrorBoundary from "./components/ErrorBoundary";
import { AuthProvider } from "./hooks/useAuth";
import { ThemeModeProvider, useThemeMode } from "./hooks/useThemeMode";
import { buildTheme } from "./theme";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000, // 30s — companies/questions don't change often
      retry: 1,
    },
  },
});

/**
 * Inner component that reads the theme mode from context and builds
 * the MUI theme. Separated so useMemo re-runs only when mode changes.
 */
function ThemedApp() {
  const { mode } = useThemeMode();
  const theme = useMemo(() => buildTheme(mode), [mode]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ErrorBoundary>
        <AuthProvider>
          <App />
        </AuthProvider>
      </ErrorBoundary>
    </ThemeProvider>
  );
}

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);

root.render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeModeProvider>
        <ThemedApp />
      </ThemeModeProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
