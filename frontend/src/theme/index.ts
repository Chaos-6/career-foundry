/**
 * Custom MUI theme — Career Foundry / BIAE.
 *
 * Design system:
 * - Navy/blue primary (trust, professionalism)
 * - Green secondary (growth, positive signals)
 * - Warm amber/red for feedback & urgency
 * - Elevated card shadows with depth hierarchy
 * - Inter typeface for modern tech aesthetic
 * - 8px rhythm across all spacing
 */

import { createTheme, alpha } from "@mui/material/styles";

// ---------------------------------------------------------------------------
// Design tokens
// ---------------------------------------------------------------------------

const navy = {
  50: "#eef2f7",
  100: "#d0dbe8",
  200: "#a8bdd4",
  300: "#7a9bbf",
  400: "#4d7aab",
  500: "#1a365d",
  600: "#152c4d",
  700: "#10213a",
  800: "#0d1f3c",
  900: "#080f1e",
};

const green = {
  50: "#f0fff4",
  100: "#c6f6d5",
  200: "#9ae6b4",
  300: "#68d391",
  400: "#48bb78",
  500: "#38a169",
  600: "#2f855a",
  700: "#276749",
  800: "#22543d",
  900: "#1c4532",
};

const SHADOW_SM = "0 1px 2px 0 rgba(0,0,0,0.05)";
const SHADOW_MD =
  "0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05)";
const SHADOW_LG =
  "0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04)";
const SHADOW_XL =
  "0 20px 25px -5px rgba(0,0,0,0.08), 0 8px 10px -6px rgba(0,0,0,0.04)";

// ---------------------------------------------------------------------------
// Theme
// ---------------------------------------------------------------------------

const theme = createTheme({
  palette: {
    primary: {
      main: navy[500],
      light: "#2b6cb0",
      dark: navy[800],
      contrastText: "#ffffff",
    },
    secondary: {
      main: green[500],
      light: green[300],
      dark: green[700],
      contrastText: "#ffffff",
    },
    error: {
      main: "#e53e3e",
      light: "#fc8181",
      dark: "#c53030",
    },
    warning: {
      main: "#d69e2e",
      light: "#f6e05e",
      dark: "#b7791f",
    },
    info: {
      main: "#3182ce",
      light: "#63b3ed",
      dark: "#2c5282",
    },
    success: {
      main: green[500],
      light: green[200],
      dark: green[700],
    },
    background: {
      default: "#f7fafc",
      paper: "#ffffff",
    },
    text: {
      primary: "#1a202c",
      secondary: "#718096",
    },
    divider: alpha("#1a365d", 0.08),
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica Neue", Arial, sans-serif',
    h1: { fontWeight: 800, letterSpacing: "-0.025em" },
    h2: { fontWeight: 700, letterSpacing: "-0.02em" },
    h3: { fontWeight: 700, letterSpacing: "-0.015em" },
    h4: { fontWeight: 700, letterSpacing: "-0.01em" },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    subtitle1: { fontWeight: 500 },
    button: { fontWeight: 600, letterSpacing: "0.01em" },
  },
  shape: {
    borderRadius: 10,
  },
  shadows: [
    "none",
    SHADOW_SM,
    SHADOW_SM,
    SHADOW_MD,
    SHADOW_MD,
    SHADOW_LG,
    SHADOW_LG,
    SHADOW_LG,
    SHADOW_XL,
    SHADOW_XL,
    SHADOW_XL,
    SHADOW_XL,
    SHADOW_XL,
    SHADOW_XL,
    SHADOW_XL,
    SHADOW_XL,
    SHADOW_XL,
    SHADOW_XL,
    SHADOW_XL,
    SHADOW_XL,
    SHADOW_XL,
    SHADOW_XL,
    SHADOW_XL,
    SHADOW_XL,
    SHADOW_XL,
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          fontWeight: 600,
          borderRadius: 8,
          transition: "all 0.15s ease",
        },
        contained: {
          boxShadow: SHADOW_SM,
          "&:hover": {
            boxShadow: SHADOW_MD,
            transform: "translateY(-1px)",
          },
          "&:active": {
            transform: "translateY(0)",
          },
        },
        outlined: {
          "&:hover": {
            transform: "translateY(-1px)",
          },
        },
        sizeLarge: {
          padding: "12px 28px",
          fontSize: "1rem",
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: SHADOW_MD,
          borderRadius: 12,
          transition: "box-shadow 0.2s ease, transform 0.2s ease",
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
          borderRadius: 8,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none", // Remove MUI default gradient overlay
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          "& .MuiOutlinedInput-root": {
            transition: "box-shadow 0.15s ease",
            "&.Mui-focused": {
              boxShadow: `0 0 0 3px ${alpha(navy[500], 0.12)}`,
            },
          },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: {
          "& .MuiOutlinedInput-notchedOutline": {
            transition: "border-color 0.15s ease",
          },
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 10,
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          "&.MuiTableRow-hover:hover": {
            backgroundColor: alpha(navy[500], 0.03),
          },
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          marginLeft: 8,
          marginRight: 8,
          "&.Mui-selected": {
            backgroundColor: alpha(navy[500], 0.08),
            "&:hover": {
              backgroundColor: alpha(navy[500], 0.12),
            },
          },
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: "none",
          boxShadow: "1px 0 0 0 rgba(0,0,0,0.04)",
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: "0 1px 0 0 rgba(0,0,0,0.06)",
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          borderRadius: 6,
          fontSize: 12,
          fontWeight: 500,
        },
      },
    },
  },
});

export default theme;
