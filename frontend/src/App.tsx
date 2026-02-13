/**
 * App root — React Router setup with Layout wrapper.
 *
 * Routes:
 * - /                Dashboard
 * - /evaluate         New Evaluation form
 * - /evaluations/:id  Evaluation results
 * - /mock             Mock Interview (timed practice)
 * - /generator        AI Answer Generator
 * - /questions        Question Bank
 */

import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import NewEvaluation from "./pages/NewEvaluation";
import EvaluationDetail from "./pages/EvaluationDetail";
import MockInterview from "./pages/MockInterview";
import AnswerGenerator from "./pages/AnswerGenerator";
import QuestionBank from "./pages/QuestionBank";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/evaluate" element={<NewEvaluation />} />
          <Route path="/evaluations/:id" element={<EvaluationDetail />} />
          <Route path="/mock" element={<MockInterview />} />
          <Route path="/generator" element={<AnswerGenerator />} />
          <Route path="/questions" element={<QuestionBank />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
