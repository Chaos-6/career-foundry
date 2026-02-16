/**
 * Login & Register page — email/password + OAuth (Google, GitHub).
 *
 * Why a single page instead of two?
 *   - Users frequently switch between "I have an account" and "I need one"
 *   - A single page avoids route navigation during a frustration-prone flow
 *   - The forms share the same layout, reducing code duplication
 *
 * OAuth flow:
 *   The backend redirects to this page with tokens in the URL fragment
 *   (#access_token=...&refresh_token=...). The useEffect on mount checks
 *   for this fragment, stores the tokens, and redirects to the dashboard.
 *   Fragments are never sent to the server, keeping tokens off access logs.
 *
 * After successful auth, redirects to the page the user was trying to reach
 * (via React Router's `state.from` pattern) or to the dashboard.
 */

import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  Link,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import GoogleIcon from "@mui/icons-material/Google";
import GitHubIcon from "@mui/icons-material/GitHub";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import { useAuth } from "../hooks/useAuth";
import { setTokens } from "../api/client";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const [tab, setTab] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { login, register, hydrate } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Where to redirect after auth — defaults to dashboard
  const from = (location.state as { from?: string })?.from || "/";

  // ---------------------------------------------------------------------------
  // Handle OAuth redirect — tokens arrive in the URL fragment
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const hash = window.location.hash;
    if (!hash || !hash.includes("access_token")) return;

    // Parse fragment params: #access_token=xxx&refresh_token=yyy
    const params = new URLSearchParams(hash.substring(1));
    const accessToken = params.get("access_token");
    const refreshToken = params.get("refresh_token");

    if (accessToken && refreshToken) {
      // Store tokens and refresh auth state
      setTokens(accessToken, refreshToken);
      // Clear the fragment from the URL (security hygiene)
      window.history.replaceState(null, "", window.location.pathname);
      // Re-hydrate the auth context so useAuth picks up the new tokens
      hydrate();
      navigate(from, { replace: true });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ---------------------------------------------------------------------------
  // Email/password auth
  // ---------------------------------------------------------------------------
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !password) {
      setError("Email and password are required.");
      return;
    }

    if (tab === "register") {
      if (password.length < 8) {
        setError("Password must be at least 8 characters.");
        return;
      }
      if (password !== confirmPassword) {
        setError("Passwords do not match.");
        return;
      }
    }

    setLoading(true);
    try {
      if (tab === "login") {
        await login(email, password);
      } else {
        await register(email, password, displayName || undefined);
      }
      navigate(from, { replace: true });
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "Something went wrong. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setError(null);
    setPassword("");
    setConfirmPassword("");
  };

  // ---------------------------------------------------------------------------
  // OAuth handlers — redirect to backend which redirects to provider
  // ---------------------------------------------------------------------------
  const handleGoogleLogin = () => {
    window.location.href = `${API_BASE}/auth/oauth/google`;
  };

  const handleGithubLogin = () => {
    window.location.href = `${API_BASE}/auth/oauth/github`;
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        bgcolor: "background.default",
        px: 2,
      }}
    >
      {/* Branding */}
      <Stack alignItems="center" sx={{ mb: 4 }}>
        <Box
          sx={{
            width: 52,
            height: 52,
            borderRadius: "14px",
            bgcolor: "primary.main",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            mb: 2,
          }}
        >
          <SmartToyIcon sx={{ color: "white", fontSize: 28 }} />
        </Box>
        <Typography
          variant="h4"
          fontWeight={800}
          color="text.primary"
          gutterBottom
          sx={{ letterSpacing: "-0.02em" }}
        >
          Career Foundry
        </Typography>
        <Typography variant="body1" color="text.secondary" textAlign="center" sx={{ maxWidth: 320 }}>
          AI-powered interview coaching. Practice answers. Get scored feedback. Land the job.
        </Typography>
      </Stack>

      {/* Auth card */}
      <Card sx={{ width: "100%", maxWidth: 440 }}>
        <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
          <Tabs
            value={tab}
            onChange={(_, v) => {
              setTab(v);
              resetForm();
            }}
            variant="fullWidth"
            sx={{ mb: 3 }}
          >
            <Tab label="Sign In" value="login" />
            <Tab label="Create Account" value="register" />
          </Tabs>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {/* OAuth buttons */}
          <Stack spacing={1.5} sx={{ mb: 2 }}>
            <Button
              variant="outlined"
              fullWidth
              startIcon={<GoogleIcon />}
              onClick={handleGoogleLogin}
              sx={{
                py: 1.2,
                textTransform: "none",
                borderColor: "divider",
                color: "text.primary",
                "&:hover": { borderColor: "primary.main", bgcolor: "action.hover" },
              }}
            >
              Continue with Google
            </Button>
            <Button
              variant="outlined"
              fullWidth
              startIcon={<GitHubIcon />}
              onClick={handleGithubLogin}
              sx={{
                py: 1.2,
                textTransform: "none",
                borderColor: "divider",
                color: "text.primary",
                "&:hover": { borderColor: "text.primary", bgcolor: "action.hover" },
              }}
            >
              Continue with GitHub
            </Button>
          </Stack>

          <Divider sx={{ my: 2 }}>
            <Typography variant="caption" color="text.secondary">
              OR
            </Typography>
          </Divider>

          {/* Email/password form */}
          <form onSubmit={handleSubmit}>
            <Stack spacing={2}>
              {tab === "register" && (
                <TextField
                  label="Display Name"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  fullWidth
                  autoComplete="name"
                  placeholder="How should we address you?"
                />
              )}

              <TextField
                label="Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                fullWidth
                autoComplete="email"
              />

              <TextField
                label="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                fullWidth
                autoComplete={
                  tab === "login" ? "current-password" : "new-password"
                }
                helperText={
                  tab === "register" ? "Minimum 8 characters" : undefined
                }
              />

              {tab === "register" && (
                <TextField
                  label="Confirm Password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  fullWidth
                  autoComplete="new-password"
                />
              )}

              <Button
                type="submit"
                variant="contained"
                size="large"
                fullWidth
                disabled={loading}
                sx={{ py: 1.5, mt: 1 }}
              >
                {loading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : tab === "login" ? (
                  "Sign In"
                ) : (
                  "Create Account"
                )}
              </Button>
            </Stack>
          </form>

          <Divider sx={{ my: 3 }} />

          <Typography variant="body2" color="text.secondary" textAlign="center">
            {tab === "login" ? (
              <>
                Don't have an account?{" "}
                <Link
                  component="button"
                  variant="body2"
                  onClick={() => {
                    setTab("register");
                    resetForm();
                  }}
                >
                  Create one
                </Link>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <Link
                  component="button"
                  variant="body2"
                  onClick={() => {
                    setTab("login");
                    resetForm();
                  }}
                >
                  Sign in
                </Link>
              </>
            )}
          </Typography>
        </CardContent>
      </Card>

      {/* Skip auth link for browsing */}
      <Typography
        variant="body2"
        color="text.secondary"
        sx={{ mt: 2, textAlign: "center" }}
      >
        <Link
          component="button"
          variant="body2"
          color="text.secondary"
          onClick={() => navigate("/")}
          sx={{ textDecoration: "underline" }}
        >
          Continue without signing in
        </Link>
      </Typography>
    </Box>
  );
}
