/**
 * Route guard — redirects unauthenticated users to /login.
 *
 * Passes the attempted URL via `state.from` so LoginPage can redirect
 * back after successful auth.
 *
 * Why a wrapper component instead of a hook?
 *   React Router v6+ recommends the "layout route" pattern for guards.
 *   Wrapping <Outlet /> lets us protect entire route subtrees without
 *   adding guard logic to every page component.
 */

import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { Box, CircularProgress } from "@mui/material";
import { useAuth } from "../hooks/useAuth";

export default function ProtectedRoute({
  children,
}: {
  children: React.ReactElement;
}) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  // While hydrating auth state from stored token, show a spinner
  if (loading) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "50vh",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  return children;
}
