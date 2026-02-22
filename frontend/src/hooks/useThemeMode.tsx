/**
 * Theme mode context — light/dark toggle with localStorage persistence.
 *
 * Wrap the app with <ThemeModeProvider> and call useThemeMode() anywhere
 * to read/toggle the current mode.
 *
 * The mode is stored in localStorage under "cf_theme_mode" so it persists
 * across page reloads. Defaults to "light" if no preference is stored.
 */

import React, { createContext, useContext, useMemo, useState, useCallback } from "react";
import type { PaletteMode } from "@mui/material";

const STORAGE_KEY = "cf_theme_mode";

interface ThemeModeContextValue {
  mode: PaletteMode;
  toggleMode: () => void;
}

const ThemeModeContext = createContext<ThemeModeContextValue>({
  mode: "light",
  toggleMode: () => {},
});

function getInitialMode(): PaletteMode {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "dark" || stored === "light") return stored;
  } catch {
    // localStorage not available (SSR, privacy mode)
  }
  return "light";
}

export function ThemeModeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setMode] = useState<PaletteMode>(getInitialMode);

  const toggleMode = useCallback(() => {
    setMode((prev) => {
      const next = prev === "light" ? "dark" : "light";
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch {
        // Silently fail
      }
      return next;
    });
  }, []);

  const value = useMemo(() => ({ mode, toggleMode }), [mode, toggleMode]);

  return (
    <ThemeModeContext.Provider value={value}>
      {children}
    </ThemeModeContext.Provider>
  );
}

export function useThemeMode() {
  return useContext(ThemeModeContext);
}
