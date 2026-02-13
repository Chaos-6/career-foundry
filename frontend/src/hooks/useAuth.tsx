/**
 * Auth context provider — manages JWT tokens and user state.
 *
 * How it works:
 * - Tokens stored in localStorage (survives page refresh)
 * - On mount, reads stored access token and calls GET /auth/me to hydrate user
 * - Provides login(), register(), logout(), and isAuthenticated
 * - The axios interceptor in client.ts handles token attachment + 401 refresh
 *
 * Why React Context (not Redux/Zustand)?
 *   Auth state is simple (user + loading flag). The rest of the app uses
 *   React Query for server state, so adding a state library just for auth
 *   would be over-engineering.
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  loginUser,
  registerUser,
  getMe,
  getAccessToken,
  setTokens,
  clearTokens,
} from "../api/client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AuthUser {
  id: string;
  email: string;
  display_name: string | null;
  default_role: string | null;
  default_experience_level: string | null;
  plan_tier: string;
  evaluations_this_month: number;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    displayName?: string
  ) => Promise<void>;
  logout: () => void;
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true); // true until initial hydration completes

  // Hydrate user from stored token on mount
  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setLoading(false);
      return;
    }

    getMe()
      .then((u) => setUser(u))
      .catch(() => {
        // Token expired or invalid — clear and continue as logged-out
        clearTokens();
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await loginUser({ email, password });
    setTokens(tokens.access_token, tokens.refresh_token);
    const me = await getMe();
    setUser(me);
  }, []);

  const register = useCallback(
    async (email: string, password: string, displayName?: string) => {
      const tokens = await registerUser({
        email,
        password,
        display_name: displayName,
      });
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await getMe();
      setUser(me);
    },
    []
  );

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: !!user,
      login,
      register,
      logout,
    }),
    [user, loading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
