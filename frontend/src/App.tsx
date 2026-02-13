/**
 * App root — React Router setup with Layout wrapper and auth routing.
 *
 * Route structure:
 * - /login            Login/Register (no layout, full-page)
 * - /                 Dashboard (public — shows feature cards)
 * - /evaluate         New Evaluation (protected)
 * - /evaluations/:id  Evaluation results (protected)
 * - /mock             Mock Interview (protected)
 * - /generator        AI Answer Generator (protected)
 * - /questions        Question Bank (public — browsing is free)
 * - /analytics        Advanced Analytics (protected)
 *
 * Why some routes are public:
 *   The dashboard and question bank are discovery surfaces. Letting
 *   users see what's available before signing up reduces friction.
 *   The actual "do work" routes (evaluate, mock, generator) require auth
 *   so we can track history and usage.
 */

import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Dashboard from "./pages/Dashboard";
import LoginPage from "./pages/LoginPage";
import NewEvaluation from "./pages/NewEvaluation";
import EvaluationDetail from "./pages/EvaluationDetail";
import MockInterview from "./pages/MockInterview";
import AnswerGenerator from "./pages/AnswerGenerator";
import QuestionBank from "./pages/QuestionBank";
import VersionComparison from "./pages/VersionComparison";
import Analytics from "./pages/Analytics";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Login page — full-screen, no sidebar layout */}
        <Route path="/login" element={<LoginPage />} />

        {/* Main app with sidebar layout */}
        <Route element={<Layout />}>
          {/* Public routes */}
          <Route path="/" element={<Dashboard />} />
          <Route path="/questions" element={<QuestionBank />} />

          {/* Protected routes — require authentication */}
          <Route
            path="/evaluate"
            element={
              <ProtectedRoute>
                <NewEvaluation />
              </ProtectedRoute>
            }
          />
          <Route
            path="/evaluations/:id"
            element={
              <ProtectedRoute>
                <EvaluationDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/mock"
            element={
              <ProtectedRoute>
                <MockInterview />
              </ProtectedRoute>
            }
          />
          <Route
            path="/generator"
            element={
              <ProtectedRoute>
                <AnswerGenerator />
              </ProtectedRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <ProtectedRoute>
                <Analytics />
              </ProtectedRoute>
            }
          />
          <Route
            path="/answers/:answerId/compare"
            element={
              <ProtectedRoute>
                <VersionComparison />
              </ProtectedRoute>
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
