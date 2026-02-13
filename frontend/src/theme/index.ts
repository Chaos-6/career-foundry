/**
 * Custom MUI theme for the Behavioral Interview Answer Evaluator.
 *
 * Interview-prep palette: professional navy/blue with green accents
 * for positive scores and amber/red for areas needing work.
 */

import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    primary: {
      main: "#1a365d", // Navy
      light: "#2b6cb0",
      dark: "#0d1f3c",
    },
    secondary: {
      main: "#38a169", // Green accent
      light: "#68d391",
      dark: "#276749",
    },
    error: {
      main: "#e53e3e",
    },
    warning: {
      main: "#d69e2e",
    },
    background: {
      default: "#f7fafc",
      paper: "#ffffff",
    },
    text: {
      primary: "#2d3748",
      secondary: "#718096",
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica Neue", Arial, sans-serif',
    h4: {
      fontWeight: 700,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          fontWeight: 600,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)",
        },
      },
    },
  },
});

export default theme;
