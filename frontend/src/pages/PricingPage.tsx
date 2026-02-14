/**
 * Pricing page — free vs. Pro tier comparison with upgrade button.
 *
 * Why a dedicated pricing page?
 *   Users who hit the free tier limit need a clear path to upgrade.
 *   It also serves as a marketing page for users who want to see
 *   what they're getting before they sign up.
 *
 * The page handles three states:
 * 1. Not logged in → "Sign in to upgrade" CTA
 * 2. Free tier → "Upgrade to Pro" button → Stripe Checkout redirect
 * 3. Pro tier → "Manage Subscription" → Stripe Customer Portal
 *
 * After Stripe Checkout, the user lands on /billing/success which
 * shows a confirmation and refreshes their auth state.
 */

import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import StarIcon from "@mui/icons-material/Star";
import RocketLaunchIcon from "@mui/icons-material/RocketLaunch";
import { useAuth } from "../hooks/useAuth";
import { createCheckoutSession, createPortalSession } from "../api/client";

const FREE_FEATURES = [
  "5 evaluations per month",
  "Full STAR dimension scoring",
  "Company-specific coaching",
  "Question bank access",
  "AI answer generator",
];

const PRO_FEATURES = [
  "Unlimited evaluations",
  "Full STAR dimension scoring",
  "Company-specific coaching",
  "Question bank access",
  "AI answer generator",
  "Advanced analytics & radar charts",
  "Score trend tracking",
  "PDF report exports",
  "Mock interview mode",
  "Priority support",
];

export default function PricingPage() {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check if we just arrived from a successful checkout
  const isSuccess = location.pathname === "/billing/success";

  const handleUpgrade = async () => {
    if (!isAuthenticated) {
      navigate("/login", { state: { from: "/pricing" } });
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const { checkout_url } = await createCheckoutSession();
      window.location.href = checkout_url;
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail || "Failed to start checkout. Try again.";
      setError(typeof msg === "string" ? msg : msg.message || JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    setLoading(true);
    setError(null);
    try {
      const { portal_url } = await createPortalSession();
      window.location.href = portal_url;
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail || "Failed to open billing portal.";
      setError(typeof msg === "string" ? msg : msg.message || JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  const isPro = user?.plan_tier === "pro";

  return (
    <Box sx={{ maxWidth: 900, mx: "auto", py: 2 }}>
      {/* Success banner after Stripe checkout */}
      {isSuccess && (
        <Alert severity="success" sx={{ mb: 3 }}>
          <strong>Welcome to Pro!</strong> Your upgrade is complete. You now
          have unlimited evaluations.
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Typography variant="h4" fontWeight={700} textAlign="center" gutterBottom>
        Choose Your Plan
      </Typography>
      <Typography
        variant="body1"
        color="text.secondary"
        textAlign="center"
        sx={{ mb: 4, maxWidth: 600, mx: "auto" }}
      >
        Get AI-powered feedback on your behavioral interview answers.
        Start free, upgrade when you're ready.
      </Typography>

      {/* Tier cards */}
      <Stack
        direction={{ xs: "column", md: "row" }}
        spacing={3}
        justifyContent="center"
        alignItems="stretch"
      >
        {/* Free tier */}
        <Card
          sx={{
            flex: 1,
            maxWidth: 400,
            border: isPro ? undefined : "2px solid",
            borderColor: isPro ? undefined : "primary.main",
          }}
        >
          <CardContent sx={{ p: 4 }}>
            <Stack spacing={2}>
              <Box>
                <Typography variant="h5" fontWeight={700}>
                  Free
                </Typography>
                <Typography variant="h3" fontWeight={700} color="text.primary">
                  $0
                  <Typography
                    component="span"
                    variant="h6"
                    color="text.secondary"
                  >
                    /month
                  </Typography>
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Perfect for getting started
                </Typography>
              </Box>

              {!isPro && isAuthenticated && (
                <Chip label="Current Plan" color="primary" size="small" />
              )}

              <Divider />

              <List dense disablePadding>
                {FREE_FEATURES.map((feature) => (
                  <ListItem key={feature} disableGutters sx={{ py: 0.5 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <CheckCircleIcon color="success" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary={feature}
                      primaryTypographyProps={{ variant: "body2" }}
                    />
                  </ListItem>
                ))}
              </List>

              {!isAuthenticated && (
                <Button
                  variant="outlined"
                  size="large"
                  fullWidth
                  onClick={() => navigate("/login")}
                  sx={{ mt: 2 }}
                >
                  Get Started Free
                </Button>
              )}
            </Stack>
          </CardContent>
        </Card>

        {/* Pro tier */}
        <Card
          sx={{
            flex: 1,
            maxWidth: 400,
            border: "2px solid",
            borderColor: isPro ? "primary.main" : "divider",
            position: "relative",
            overflow: "visible",
          }}
        >
          {/* Popular badge */}
          <Chip
            icon={<StarIcon />}
            label="Most Popular"
            color="primary"
            size="small"
            sx={{
              position: "absolute",
              top: -12,
              left: "50%",
              transform: "translateX(-50%)",
            }}
          />

          <CardContent sx={{ p: 4 }}>
            <Stack spacing={2}>
              <Box>
                <Typography variant="h5" fontWeight={700} color="primary.main">
                  Pro
                </Typography>
                <Typography variant="h3" fontWeight={700} color="text.primary">
                  $12
                  <Typography
                    component="span"
                    variant="h6"
                    color="text.secondary"
                  >
                    /month
                  </Typography>
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  For serious interview prep
                </Typography>
              </Box>

              {isPro && (
                <Chip label="Current Plan" color="primary" size="small" />
              )}

              <Divider />

              <List dense disablePadding>
                {PRO_FEATURES.map((feature) => (
                  <ListItem key={feature} disableGutters sx={{ py: 0.5 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <CheckCircleIcon color="success" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary={feature}
                      primaryTypographyProps={{ variant: "body2" }}
                    />
                  </ListItem>
                ))}
              </List>

              {isPro ? (
                <Button
                  variant="outlined"
                  size="large"
                  fullWidth
                  onClick={handleManageSubscription}
                  disabled={loading}
                  sx={{ mt: 2 }}
                >
                  {loading ? (
                    <CircularProgress size={24} />
                  ) : (
                    "Manage Subscription"
                  )}
                </Button>
              ) : (
                <Button
                  variant="contained"
                  size="large"
                  fullWidth
                  startIcon={<RocketLaunchIcon />}
                  onClick={handleUpgrade}
                  disabled={loading}
                  sx={{ mt: 2, py: 1.5 }}
                >
                  {loading ? (
                    <CircularProgress size={24} color="inherit" />
                  ) : (
                    "Upgrade to Pro"
                  )}
                </Button>
              )}
            </Stack>
          </CardContent>
        </Card>
      </Stack>

      {/* Usage info for logged-in users */}
      {isAuthenticated && user && (
        <Box
          sx={{
            mt: 4,
            p: 3,
            bgcolor: "background.paper",
            borderRadius: 2,
            textAlign: "center",
          }}
        >
          <Typography variant="body2" color="text.secondary">
            This month: {user.evaluations_this_month} evaluation
            {user.evaluations_this_month !== 1 ? "s" : ""} used
            {user.plan_tier === "free"
              ? " of 5 free evaluations"
              : " (unlimited)"}
          </Typography>
        </Box>
      )}
    </Box>
  );
}
