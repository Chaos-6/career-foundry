/**
 * API client — Axios instance + function-per-endpoint pattern.
 *
 * Every backend endpoint gets a typed function. The frontend never
 * constructs URLs directly — this file is the single source of truth
 * for API communication.
 *
 * Auth flow:
 * - Request interceptor attaches Bearer token from localStorage
 * - Response interceptor catches 401, refreshes token, retries original request
 * - Token helpers (getAccessToken, setTokens, clearTokens) used by useAuth hook
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// ---------------------------------------------------------------------------
// Token helpers — localStorage is the single source of truth for tokens
// ---------------------------------------------------------------------------

const ACCESS_TOKEN_KEY = "biae_access_token";
const REFRESH_TOKEN_KEY = "biae_refresh_token";

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

// ---------------------------------------------------------------------------
// Request interceptor — attach Bearer token to every request
// ---------------------------------------------------------------------------

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---------------------------------------------------------------------------
// Response interceptor — refresh token on 401, retry original request
//
// Handles concurrent 401s: only one refresh in flight at a time.
// Other requests queue up and retry once the refresh completes.
// ---------------------------------------------------------------------------

let isRefreshing = false;
let pendingRequests: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

function onRefreshComplete(newToken: string) {
  pendingRequests.forEach((p) => p.resolve(newToken));
  pendingRequests = [];
}

function onRefreshFailed(err: unknown) {
  pendingRequests.forEach((p) => p.reject(err));
  pendingRequests = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Only intercept 401s, and don't retry auth endpoints or already-retried requests
    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry ||
      originalRequest.url?.startsWith("/auth/")
    ) {
      return Promise.reject(error);
    }

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      clearTokens();
      return Promise.reject(error);
    }

    if (isRefreshing) {
      // Another request is already refreshing — queue this one
      return new Promise((resolve, reject) => {
        pendingRequests.push({
          resolve: (token: string) => {
            originalRequest._retry = true;
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            resolve(api(originalRequest));
          },
          reject,
        });
      });
    }

    isRefreshing = true;
    originalRequest._retry = true;

    try {
      // Call refresh endpoint directly (not through intercepted api instance)
      const { data } = await axios.post<TokenResponse>(
        `${API_BASE}/auth/refresh`,
        { refresh_token: refreshToken }
      );

      setTokens(data.access_token, data.refresh_token);
      onRefreshComplete(data.access_token);

      // Retry original request with new token
      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
      }
      return api(originalRequest);
    } catch (refreshError) {
      onRefreshFailed(refreshError);
      clearTokens();
      // Redirect to login if refresh fails
      window.location.href = "/login";
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

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
  source: string;
  usage_count: number;
  track: string;               // "standard" | "agentic"
  interview_type: string;      // "behavioral" | "system_design"
  tags: string[];
  ideal_answer_points: string[];
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

export interface AgenticScores {
  [dimension: string]: number;  // dimension_name → 0-100
}

export interface AgenticResult {
  scores: AgenticScores;
  hiring_decision: string;
  summary_feedback?: string;
  feedback_summary?: string;
  red_flags?: string[];
  missing_components?: string[];
  the_diff: {
    user_answer_critique?: string;
    staff_engineer_rewrite?: string;
    candidate_approach?: string;
    staff_architect_approach?: string;
  };
}

export interface Evaluation {
  id: string;
  answer_version_id: string;
  answer_id: string | null;        // parent answer — for revision flow
  answer_text: string | null;      // the answer text that was evaluated
  version_number: number | null;   // which version this evaluation is for
  question_id: string | null;      // source question — for "back to question" link
  question_text: string | null;    // resolved question text (bank or custom)
  status: "queued" | "analyzing" | "completed" | "failed";
  evaluation_type: string;         // "standard" | "agentic"

  // Standard STAR scores (1-5)
  situation_score: number | null;
  task_score: number | null;
  action_score: number | null;
  result_score: number | null;
  engagement_score: number | null;
  overall_score: number | null;
  average_score: number | null;

  // Agentic scores (0-100)
  agentic_scores: AgenticScores | null;
  agentic_result: AgenticResult | null;
  hiring_decision: string | null;

  evaluation_markdown: string | null;
  evaluation_sections: Record<string, any> | null;
  company_alignment: Record<string, any> | null;
  follow_up_questions: Array<Record<string, any>> | null;
  model_used: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  processing_seconds: number | null;
  error_message: string | null;
  share_token: string | null;
  shared_at: string | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Auth types
// ---------------------------------------------------------------------------

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthUser {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  oauth_provider: string | null;
  default_role: string | null;
  default_experience_level: string | null;
  plan_tier: string;
  evaluations_this_month: number;
  is_moderator: boolean;
}

// ---------------------------------------------------------------------------
// Auth endpoints
// ---------------------------------------------------------------------------

export async function loginUser(payload: {
  email: string;
  password: string;
}): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/auth/login", payload);
  return data;
}

export async function registerUser(payload: {
  email: string;
  password: string;
  display_name?: string;
}): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/auth/register", payload);
  return data;
}

export async function refreshTokens(refreshToken: string): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/auth/refresh", {
    refresh_token: refreshToken,
  });
  return data;
}

export async function getMe(): Promise<AuthUser> {
  const { data } = await api.get<AuthUser>("/auth/me");
  return data;
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

// Community question submission
export async function submitQuestion(payload: {
  question_text: string;
  role_tags?: string[];
  company_tags?: string[];
  competency_tags?: string[];
  difficulty?: string;
  level_band?: string;
}): Promise<Question> {
  const { data } = await api.post<Question>("/api/v1/questions", payload);
  return data;
}

// ---------------------------------------------------------------------------
// Question Bookmarks
// ---------------------------------------------------------------------------

export async function bookmarkQuestion(questionId: string): Promise<void> {
  await api.post(`/api/v1/questions/${questionId}/bookmark`);
}

export async function unbookmarkQuestion(questionId: string): Promise<void> {
  await api.delete(`/api/v1/questions/${questionId}/bookmark`);
}

export async function getBookmarkedQuestionIds(): Promise<string[]> {
  const { data } = await api.get<string[]>("/api/v1/questions/bookmarked/ids");
  return data;
}

// Moderation types & endpoints
export interface ModerationQuestion {
  id: string;
  question_text: string;
  role_tags: string[];
  company_tags: string[];
  competency_tags: string[];
  difficulty: string;
  level_band: string | null;
  source: string;
  status: string;
  submitted_by_user_id: string | null;
  submitted_by_email: string | null;
  moderation_notes: string | null;
  moderated_at: string | null;
  created_at: string | null;
}

export async function getPendingQuestions(
  skip = 0,
  limit = 50
): Promise<ModerationQuestion[]> {
  const { data } = await api.get<ModerationQuestion[]>(
    "/api/v1/questions/moderation/pending",
    { params: { skip, limit } }
  );
  return data;
}

export async function moderateQuestion(
  questionId: string,
  payload: { action: "approve" | "reject"; notes?: string }
): Promise<ModerationQuestion> {
  const { data } = await api.patch<ModerationQuestion>(
    `/api/v1/questions/${questionId}/moderation`,
    payload
  );
  return data;
}

// ---------------------------------------------------------------------------
// Coaching endpoints
// ---------------------------------------------------------------------------

export interface CoachingRelationship {
  id: string;
  coach_id: string;
  coach_email: string;
  coach_name: string | null;
  student_id: string;
  student_email: string;
  student_name: string | null;
  status: string;
  created_at: string | null;
  accepted_at: string | null;
}

export interface StudentSummary {
  student_id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  total_evaluations: number;
  average_score: number | null;
  best_score: number | null;
  latest_evaluation_date: string | null;
  relationship_id: string;
}

export interface CoachDashboard {
  students: StudentSummary[];
  total_students: number;
  pending_invites: number;
}

export interface StudentEvaluation {
  evaluation_id: string;
  answer_id: string;
  question_text: string | null;
  company_name: string | null;
  target_role: string;
  average_score: number | null;
  situation_score: number | null;
  task_score: number | null;
  action_score: number | null;
  result_score: number | null;
  engagement_score: number | null;
  overall_score: number | null;
  status: string;
  created_at: string;
  version_number: number | null;
  coach_notes: CoachNotes | null;
}

export interface CoachNotes {
  notes: string;
  focus_areas: string[];
  coach_id: string;
  coach_name: string | null;
  updated_at: string | null;
}

// Coach endpoints
export async function inviteStudent(email: string): Promise<CoachingRelationship> {
  const { data } = await api.post<CoachingRelationship>("/api/v1/coaching/invite", { email });
  return data;
}

export async function getCoachStudents(): Promise<CoachDashboard> {
  const { data } = await api.get<CoachDashboard>("/api/v1/coaching/students");
  return data;
}

export async function getStudentEvaluations(studentId: string): Promise<StudentEvaluation[]> {
  const { data } = await api.get<StudentEvaluation[]>(
    `/api/v1/coaching/students/${studentId}/evaluations`
  );
  return data;
}

export async function updateCoachNotes(
  evaluationId: string,
  payload: { notes: string; focus_areas?: string[] }
): Promise<CoachNotes> {
  const { data } = await api.patch<CoachNotes>(
    `/api/v1/coaching/evaluations/${evaluationId}/coach-notes`,
    payload
  );
  return data;
}

// Student endpoints
export async function getMyInvites(): Promise<CoachingRelationship[]> {
  const { data } = await api.get<CoachingRelationship[]>("/api/v1/coaching/invites");
  return data;
}

export async function acceptInvite(inviteId: string): Promise<CoachingRelationship> {
  const { data } = await api.post<CoachingRelationship>(
    `/api/v1/coaching/invites/${inviteId}/accept`
  );
  return data;
}

export async function declineInvite(inviteId: string): Promise<void> {
  await api.post(`/api/v1/coaching/invites/${inviteId}/decline`);
}

export async function getMyCoaches(): Promise<CoachingRelationship[]> {
  const { data } = await api.get<CoachingRelationship[]>("/api/v1/coaching/my-coaches");
  return data;
}

export async function removeRelationship(relationshipId: string): Promise<void> {
  await api.delete(`/api/v1/coaching/relationships/${relationshipId}`);
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
// Bulk Import
// ---------------------------------------------------------------------------

export interface ImportAnswerItem {
  answer_id: string;
  question_text: string | null;
  word_count: number;
}

export interface ImportResponse {
  imported_count: number;
  total_found: number;
  answers: ImportAnswerItem[];
  errors: string[];
}

export async function importAnswers(
  file: File,
  targetCompanyId: string,
  targetRole: string,
  experienceLevel: string
): Promise<ImportResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("target_company_id", targetCompanyId);
  formData.append("target_role", targetRole);
  formData.append("experience_level", experienceLevel);

  const { data } = await api.post<ImportResponse>(
    "/api/v1/answers/import",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
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

// Sharing
export interface ShareResponse {
  share_token: string;
  share_url: string;
}

export interface SharedEvaluation {
  company_name: string | null;
  target_role: string | null;
  question_text: string | null;
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
  created_at: string;
}

export async function shareEvaluation(
  evaluationId: string
): Promise<ShareResponse> {
  const { data } = await api.post<ShareResponse>(
    `/api/v1/evaluations/${evaluationId}/share`
  );
  return data;
}

export async function revokeShare(evaluationId: string): Promise<void> {
  await api.delete(`/api/v1/evaluations/${evaluationId}/share`);
}

export async function getSharedEvaluation(
  token: string
): Promise<SharedEvaluation> {
  const { data } = await api.get<SharedEvaluation>(
    `/api/v1/evaluations/shared/${token}`
  );
  return data;
}

// ---------------------------------------------------------------------------
// Inline Suggestions
// ---------------------------------------------------------------------------

export interface SuggestionItem {
  section: string;
  suggestion: string;
  example: string;
}

export interface SuggestionsResponse {
  suggestions: SuggestionItem[];
  message?: string;
  input_tokens?: number;
  output_tokens?: number;
}

export async function getEvaluationSuggestions(
  evaluationId: string
): Promise<SuggestionsResponse> {
  const { data } = await api.post<SuggestionsResponse>(
    `/api/v1/evaluations/${evaluationId}/suggestions`
  );
  return data;
}

// ---------------------------------------------------------------------------
// Dashboard endpoints
// ---------------------------------------------------------------------------

export interface BadgeInfo {
  id: string;
  name: string;
  description: string;
  icon: string;
  unlocked: boolean;
  unlocked_at: string | null;
}

export interface StreakInfo {
  current_streak: number;
  longest_streak: number;
  last_practice_date: string | null;
  streak_active: boolean;
}

export interface DashboardStats {
  total_evaluations: number;
  average_score: number | null;
  best_score: number | null;
  total_answers: number;
  evaluations_this_month: number;
  streak: StreakInfo | null;
  badges: BadgeInfo[];
}

export interface RecentEvaluation {
  evaluation_id: string;
  answer_id: string;
  question_text: string | null;
  company_name: string | null;
  target_role: string;
  average_score: number | null;
  status: string;
  created_at: string;
  version_number: number | null;
}

export interface ScoreDataPoint {
  evaluation_id: string;
  date: string;
  situation: number | null;
  task: number | null;
  action: number | null;
  result: number | null;
  engagement: number | null;
  overall: number | null;
  average: number | null;
  company_name: string | null;
  target_role: string | null;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>("/api/v1/dashboard/stats");
  return data;
}

export async function getRecentEvaluations(
  limit = 10
): Promise<RecentEvaluation[]> {
  const { data } = await api.get<RecentEvaluation[]>(
    "/api/v1/dashboard/recent",
    { params: { limit } }
  );
  return data;
}

export async function getScoreHistory(
  limit = 30
): Promise<ScoreDataPoint[]> {
  const { data } = await api.get<ScoreDataPoint[]>(
    "/api/v1/dashboard/score-history",
    { params: { limit } }
  );
  return data;
}

// ---------------------------------------------------------------------------
// Recommended Questions (Spaced Repetition)
// ---------------------------------------------------------------------------

export interface RecommendedQuestion {
  question_id: string | null;
  question_text: string;
  company_name: string;
  target_role: string;
  best_score: number;
  last_practiced: string;
  days_since_practice: number;
  priority: number;
  answer_id: string;
}

export async function getRecommendedQuestions(
  limit = 5
): Promise<RecommendedQuestion[]> {
  const { data } = await api.get<RecommendedQuestion[]>(
    "/api/v1/dashboard/recommended",
    { params: { limit } }
  );
  return data;
}

// ---------------------------------------------------------------------------
// Analytics endpoints
// ---------------------------------------------------------------------------

export interface DimensionAverage {
  dimension: string;
  average: number;
  count: number;
}

export interface CompanyBreakdown {
  company_name: string;
  evaluation_count: number;
  average_score: number | null;
  best_score: number | null;
  situation_avg: number | null;
  task_avg: number | null;
  action_avg: number | null;
  result_avg: number | null;
  engagement_avg: number | null;
  overall_avg: number | null;
}

export interface ReadinessScore {
  overall_readiness: number;
  score_component: number;
  consistency_component: number;
  trend_component: number;
  label: string;
}

export interface AnalyticsData {
  dimension_averages: DimensionAverage[];
  company_breakdowns: CompanyBreakdown[];
  readiness: ReadinessScore | null;
}

export async function getAnalytics(): Promise<AnalyticsData> {
  const { data } = await api.get<AnalyticsData>("/api/v1/dashboard/analytics");
  return data;
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

// ---------------------------------------------------------------------------
// Billing endpoints
// ---------------------------------------------------------------------------

export interface BillingStatus {
  plan_tier: string;
  evaluations_this_month: number;
  evaluation_limit: number;
  stripe_customer_id: string | null;
}

export interface CheckoutResponse {
  checkout_url: string;
}

export async function getBillingStatus(): Promise<BillingStatus> {
  const { data } = await api.get<BillingStatus>("/billing/status");
  return data;
}

export async function createCheckoutSession(): Promise<CheckoutResponse> {
  const { data } = await api.post<CheckoutResponse>("/billing/checkout");
  return data;
}

export async function createPortalSession(): Promise<{ portal_url: string }> {
  const { data } = await api.post<{ portal_url: string }>("/billing/portal");
  return data;
}

// ---------------------------------------------------------------------------
// Answer Template endpoints
// ---------------------------------------------------------------------------

export interface AnswerTemplate {
  id: string;
  user_id: string;
  name: string;
  template_text: string;
  role_tags: string[];
  competency_tags: string[];
  is_default: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export async function listTemplates(): Promise<AnswerTemplate[]> {
  const { data } = await api.get<AnswerTemplate[]>("/api/v1/templates");
  return data;
}

export async function getTemplate(id: string): Promise<AnswerTemplate> {
  const { data } = await api.get<AnswerTemplate>(`/api/v1/templates/${id}`);
  return data;
}

export async function createTemplate(payload: {
  name: string;
  template_text: string;
  role_tags?: string[];
  competency_tags?: string[];
  is_default?: boolean;
}): Promise<AnswerTemplate> {
  const { data } = await api.post<AnswerTemplate>("/api/v1/templates", payload);
  return data;
}

export async function updateTemplate(
  id: string,
  payload: {
    name?: string;
    template_text?: string;
    role_tags?: string[];
    competency_tags?: string[];
    is_default?: boolean;
  }
): Promise<AnswerTemplate> {
  const { data } = await api.put<AnswerTemplate>(
    `/api/v1/templates/${id}`,
    payload
  );
  return data;
}

export async function deleteTemplate(id: string): Promise<void> {
  await api.delete(`/api/v1/templates/${id}`);
}

// ---------------------------------------------------------------------------
// Agentic Scenarios endpoints
// ---------------------------------------------------------------------------

export interface Scenario {
  id: string;
  track: string;
  type: string;             // "behavioral" | "system_design"
  role: string;
  category: string;
  difficulty: string;
  question: string;
  tags: string[];
  ideal_answer_points: string[];
}

export interface ScenarioList {
  items: Scenario[];
  total: number;
}

export async function listScenarios(params?: {
  track?: string;
  role?: string;
  category?: string;
  interview_type?: string;
  difficulty?: string;
}): Promise<ScenarioList> {
  const { data } = await api.get<ScenarioList>("/api/v1/scenarios", { params });
  return data;
}

export async function getRandomScenario(params?: {
  track?: string;
  category?: string;
  interview_type?: string;
  difficulty?: string;
}): Promise<Scenario> {
  const { data } = await api.get<Scenario>("/api/v1/scenarios/random", { params });
  return data;
}

export async function getScenarioCategories(
  track = "agentic",
  interviewType?: string,
): Promise<string[]> {
  const { data } = await api.get<string[]>("/api/v1/scenarios/categories", {
    params: { track, interview_type: interviewType || undefined },
  });
  return data;
}

export default api;
