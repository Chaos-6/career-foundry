/**
 * Login & Register page — handles both auth flows with a tab toggle.
 *
 * Why a single page instead of two?
 *   - Users frequently switch between "I have an account" and "I need one"
 *   - A single page avoids route navigation during a frustration-prone flow
 *   - The forms share the same layout, reducing code duplication
 *
 * After successful auth, redirects to the page the user was trying to reach
 * (via React Router's `state.from` pattern) or to the dashboard.
 */

import React, { useState } from "react";
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
import { useAuth } from "../hooks/useAuth";

export default function LoginPage() {
  const [tab, setTab] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Where to redirect after auth — defaults to dashboard
  const from = (location.state as { from?: string })?.from || "/";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Basic validation
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
      // Extract error message from API response
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
      <Stack alignItems="center" sx={{ mb: 3 }}>
        <Typography
          variant="h4"
          fontWeight={700}
          color="primary.main"
          gutterBottom
        >
          BIAE
        </Typography>
        <Typography variant="body1" color="text.secondary" textAlign="center">
          AI-powered STAR answer coaching for tech interviews
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
                autoFocus
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
