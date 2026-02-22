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
 *
 * Supports light + dark modes via buildTheme(mode).
 */

import { createTheme, alpha, type PaletteMode } from "@mui/material/styles";

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

// Dark mode shadow variants — slightly more diffused for dark backgrounds
const SHADOW_SM_DARK = "0 1px 3px 0 rgba(0,0,0,0.25)";
const SHADOW_MD_DARK =
  "0 4px 8px -1px rgba(0,0,0,0.3), 0 2px 4px -2px rgba(0,0,0,0.2)";
const SHADOW_LG_DARK =
  "0 10px 20px -3px rgba(0,0,0,0.35), 0 4px 8px -4px rgba(0,0,0,0.2)";
const SHADOW_XL_DARK =
  "0 20px 30px -5px rgba(0,0,0,0.4), 0 8px 12px -6px rgba(0,0,0,0.25)";

// ---------------------------------------------------------------------------
// Theme builder
// ---------------------------------------------------------------------------

export function buildTheme(mode: PaletteMode) {
  const isDark = mode === "dark";

  const shadowSm = isDark ? SHADOW_SM_DARK : SHADOW_SM;
  const shadowMd = isDark ? SHADOW_MD_DARK : SHADOW_MD;
  const shadowLg = isDark ? SHADOW_LG_DARK : SHADOW_LG;
  const shadowXl = isDark ? SHADOW_XL_DARK : SHADOW_XL;

  return createTheme({
    palette: {
      mode,
      primary: {
        main: isDark ? "#4d7aab" : navy[500],
        light: isDark ? "#6b9fd4" : "#2b6cb0",
        dark: isDark ? navy[600] : navy[800],
        contrastText: "#ffffff",
      },
      secondary: {
        main: green[500],
        light: green[300],
        dark: green[700],
        contrastText: "#ffffff",
      },
      error: {
        main: isDark ? "#fc8181" : "#e53e3e",
        light: "#fc8181",
        dark: "#c53030",
      },
      warning: {
        main: isDark ? "#f6e05e" : "#d69e2e",
        light: "#f6e05e",
        dark: "#b7791f",
      },
      info: {
        main: isDark ? "#63b3ed" : "#3182ce",
        light: "#63b3ed",
        dark: "#2c5282",
      },
      success: {
        main: green[500],
        light: green[200],
        dark: green[700],
      },
      background: {
        default: isDark ? "#0d1117" : "#f7fafc",
        paper: isDark ? "#161b22" : "#ffffff",
      },
      text: {
        primary: isDark ? "#e6edf3" : "#1a202c",
        secondary: isDark ? "#8b949e" : "#718096",
      },
      divider: isDark
        ? alpha("#e6edf3", 0.08)
        : alpha("#1a365d", 0.08),
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
      shadowSm,
      shadowSm,
      shadowMd,
      shadowMd,
      shadowLg,
      shadowLg,
      shadowLg,
      shadowXl,
      shadowXl,
      shadowXl,
      shadowXl,
      shadowXl,
      shadowXl,
      shadowXl,
      shadowXl,
      shadowXl,
      shadowXl,
      shadowXl,
      shadowXl,
      shadowXl,
      shadowXl,
      shadowXl,
      shadowXl,
      shadowXl,
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
            boxShadow: shadowSm,
            "&:hover": {
              boxShadow: shadowMd,
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
            boxShadow: shadowMd,
            borderRadius: 12,
            transition: "box-shadow 0.2s ease, transform 0.2s ease",
            ...(isDark && {
              border: `1px solid ${alpha("#e6edf3", 0.06)}`,
            }),
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
                boxShadow: `0 0 0 3px ${alpha(
                  isDark ? "#4d7aab" : navy[500],
                  isDark ? 0.2 : 0.12
                )}`,
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
              backgroundColor: alpha(isDark ? "#e6edf3" : navy[500], 0.03),
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
              backgroundColor: alpha(isDark ? "#4d7aab" : navy[500], isDark ? 0.15 : 0.08),
              "&:hover": {
                backgroundColor: alpha(isDark ? "#4d7aab" : navy[500], isDark ? 0.2 : 0.12),
              },
            },
          },
        },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            borderRight: "none",
            boxShadow: isDark
              ? "1px 0 0 0 rgba(255,255,255,0.04)"
              : "1px 0 0 0 rgba(0,0,0,0.04)",
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            boxShadow: isDark
              ? "0 1px 0 0 rgba(255,255,255,0.06)"
              : "0 1px 0 0 rgba(0,0,0,0.06)",
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
}

// Default export for backward compatibility (light mode)
const theme = buildTheme("light");
export default theme;
