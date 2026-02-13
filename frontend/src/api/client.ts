/**
 * API client — Axios instance + function-per-endpoint pattern.
 *
 * Every backend endpoint gets a typed function. The frontend never
 * constructs URLs directly — this file is the single source of truth
 * for API communication.
 */

import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Company {
  id: string;
  name: string;
  slug: string;
  principle_type: string;
}

export interface CompanyDetail extends Company {
  principles: Array<{ name: string; description: string }>;
  interview_focus: string;
  interview_tips: string[] | null;
  logo_url: string | null;
}

export interface Question {
  id: string;
  question_text: string;
  role_tags: string[];
  company_tags: string[];
  competency_tags: string[];
  difficulty: string;
  level_band: string | null;
  usage_count: number;
}

export interface QuestionList {
  items: Question[];
  total: number;
  skip: number;
  limit: number;
}

export interface AnswerVersion {
  id: string;
  answer_id: string;
  version_number: number;
  answer_text: string;
  word_count: number | null;
  is_ai_assisted: boolean;
  created_at: string;
}

export interface Answer {
  id: string;
  user_id: string | null;
  question_id: string | null;
  custom_question_text: string | null;
  target_company_id: string;
  target_role: string;
  experience_level: string;
  version_count: number;
  best_average_score: number | null;
  created_at: string;
  updated_at: string;
  versions?: AnswerVersion[];
}

export interface Evaluation {
  id: string;
  answer_version_id: string;
  status: "queued" | "analyzing" | "completed" | "failed";
  situation_score: number | null;
  task_score: number | null;
  action_score: number | null;
  result_score: number | null;
  engagement_score: number | null;
  overall_score: number | null;
  average_score: number | null;
  evaluation_markdown: string | null;
  evaluation_sections: Record<string, any> | null;
  company_alignment: Record<string, any> | null;
  follow_up_questions: Array<Record<string, any>> | null;
  model_used: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  processing_seconds: number | null;
  error_message: string | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Company endpoints
// ---------------------------------------------------------------------------

export async function listCompanies(): Promise<Company[]> {
  const { data } = await api.get<Company[]>("/api/v1/companies");
  return data;
}

export async function getCompany(id: string): Promise<CompanyDetail> {
  const { data } = await api.get<CompanyDetail>(`/api/v1/companies/${id}`);
  return data;
}

// ---------------------------------------------------------------------------
// Question endpoints
// ---------------------------------------------------------------------------

export async function listQuestions(params?: {
  role?: string;
  competency?: string;
  difficulty?: string;
  level?: string;
  company?: string;
  search?: string;
  skip?: number;
  limit?: number;
}): Promise<QuestionList> {
  const { data } = await api.get<QuestionList>("/api/v1/questions", { params });
  return data;
}

export async function getRandomQuestion(params?: {
  role?: string;
  competency?: string;
  difficulty?: string;
  level?: string;
}): Promise<Question> {
  const { data } = await api.get<Question>("/api/v1/questions/random", {
    params,
  });
  return data;
}

// ---------------------------------------------------------------------------
// Answer endpoints
// ---------------------------------------------------------------------------

export async function createAnswer(payload: {
  question_id?: string;
  custom_question_text?: string;
  target_company_id: string;
  target_role: string;
  experience_level: string;
  answer_text: string;
  is_ai_assisted?: boolean;
}): Promise<Answer> {
  const { data } = await api.post<Answer>("/api/v1/answers", payload);
  return data;
}

export async function getAnswer(id: string): Promise<Answer> {
  const { data } = await api.get<Answer>(`/api/v1/answers/${id}`);
  return data;
}

export interface VersionScoreSummary {
  id: string;
  version_number: number;
  word_count: number | null;
  is_ai_assisted: boolean;
  created_at: string;
  evaluation_id: string | null;
  evaluation_status: string | null;
  situation_score: number | null;
  task_score: number | null;
  action_score: number | null;
  result_score: number | null;
  engagement_score: number | null;
  overall_score: number | null;
  average_score: number | null;
}

export interface AnswerComparison extends Answer {
  version_scores: VersionScoreSummary[];
}

export async function getAnswerComparison(
  id: string
): Promise<AnswerComparison> {
  const { data } = await api.get<AnswerComparison>(
    `/api/v1/answers/${id}/compare`
  );
  return data;
}

export async function createVersion(
  answerId: string,
  payload: { answer_text: string; is_ai_assisted?: boolean }
): Promise<AnswerVersion> {
  const { data } = await api.post<AnswerVersion>(
    `/api/v1/answers/${answerId}/versions`,
    payload
  );
  return data;
}

// ---------------------------------------------------------------------------
// Evaluation endpoints
// ---------------------------------------------------------------------------

export async function createEvaluation(
  answerVersionId: string
): Promise<Evaluation> {
  const { data } = await api.post<Evaluation>("/api/v1/evaluations", {
    answer_version_id: answerVersionId,
  });
  return data;
}

export async function getEvaluation(id: string): Promise<Evaluation> {
  const { data } = await api.get<Evaluation>(`/api/v1/evaluations/${id}`);
  return data;
}

export function getEvaluationPdfUrl(id: string): string {
  return `${API_BASE}/api/v1/evaluations/${id}/report/pdf`;
}

// ---------------------------------------------------------------------------
// Mock Interview endpoints
// ---------------------------------------------------------------------------

export interface MockSession {
  id: string;
  question_id: string;
  question_text: string;
  time_limit_seconds: number;
  time_used_seconds: number | null;
  completed: boolean;
}

export async function startMockSession(payload: {
  question_id: string;
  time_limit_seconds?: number;
}): Promise<MockSession> {
  const { data } = await api.post<MockSession>("/api/v1/mock", payload);
  return data;
}

export async function completeMockSession(
  sessionId: string,
  payload: {
    time_used_seconds: number;
    answer_version_id?: string;
    evaluation_id?: string;
  }
): Promise<MockSession> {
  const { data } = await api.patch<MockSession>(
    `/api/v1/mock/${sessionId}`,
    payload
  );
  return data;
}

// ---------------------------------------------------------------------------
// AI Generator endpoints
// ---------------------------------------------------------------------------

export interface GenerateResult {
  answer_text: string;
  word_count: number;
  model_used: string;
  input_tokens: number;
  output_tokens: number;
  processing_seconds: number;
}

export async function generateAnswer(payload: {
  question_text: string;
  company_name: string;
  target_role: string;
  experience_level: string;
  situation_bullets: string;
  task_bullets: string;
  action_bullets: string;
  result_bullets: string;
}): Promise<GenerateResult> {
  const { data } = await api.post<GenerateResult>("/api/v1/generator", payload);
  return data;
}

export default api;
