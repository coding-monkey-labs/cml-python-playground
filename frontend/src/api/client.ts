import axios from "axios";
import type {
  ActivityItem,
  AgentContext,
  AuthTokens,
  DashboardSummaryResponse,
  DefectTrends,
  DeveloperMetrics,
  DuplicateResult,
  Feature,
  FeatureHealthScore,
  FeatureMetrics,
  HotspotFeature,
  JiraIssue,
  LoginRequest,
  PRImpact,
  PullRequest,
  ReopenPattern,
  SimilarityResult,
  SystemHealth,
  User,
  WorkflowRun,
  WorkflowSchedule,
} from "@/types";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 → redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (data: LoginRequest) =>
    api.post<AuthTokens>("/auth/login", data).then((r) => r.data),

  register: (data: { email: string; password: string; full_name: string }) =>
    api.post<User>("/auth/register", data).then((r) => r.data),

  profile: () => api.get<User>("/auth/profile").then((r) => r.data),
};

// ── Dashboard ────────────────────────────────────────────────────────────────

export const dashboardApi = {
  summary: () =>
    api.get<DashboardSummaryResponse>("/dashboard/summary").then((r) => r.data),

  trends: (periods = 6) =>
    api.get<DefectTrends>("/dashboard/trends", { params: { periods } }).then((r) => r.data),

  activity: (limit = 20) =>
    api.get<ActivityItem[]>("/dashboard/activity", { params: { limit } }).then((r) => r.data),

  systemHealth: () =>
    api.get<SystemHealth>("/dashboard/system-health").then((r) => r.data),
};

// ── Features ─────────────────────────────────────────────────────────────────

export const featuresApi = {
  list: () => api.get<Feature[]>("/features").then((r) => r.data),

  tree: () => api.get<Feature[]>("/features/tree").then((r) => r.data),

  get: (id: number) => api.get<Feature>(`/features/${id}`).then((r) => r.data),

  metrics: (name: string) =>
    api.get<FeatureMetrics>(`/features/${name}/metrics`).then((r) => r.data),

  defectDensity: (name: string) =>
    api.get(`/features/${name}/defect-density`).then((r) => r.data),
};

// ── Jira ─────────────────────────────────────────────────────────────────────

export const jiraApi = {
  search: (query: string, issueType?: string, limit = 20) =>
    api
      .post<JiraIssue[]>("/jira/search", {
        query,
        issue_type: issueType || null,
        limit,
      })
      .then((r) => r.data),

  get: (key: string) => api.get<JiraIssue>(`/jira/${key}`).then((r) => r.data),

  subtree: (key: string) => api.get(`/jira/${key}/subtree`).then((r) => r.data),
};

// ── Pull Requests ────────────────────────────────────────────────────────────

export const prApi = {
  search: (repo: string, status?: string, limit = 20) =>
    api
      .get<PullRequest[]>("/pr/search", { params: { repo, status, limit } })
      .then((r) => r.data),

  impact: (repo: string, prNumber: number) =>
    api.get<PRImpact>(`/pr/${repo}/${prNumber}/impact`).then((r) => r.data),
};

// ── Analytics ────────────────────────────────────────────────────────────────

export const analyticsApi = {
  hotspots: (limit = 10) =>
    api.get<HotspotFeature[]>("/analytics/hotspots", { params: { limit } }).then((r) => r.data),

  reopenPatterns: (limit = 10) =>
    api
      .get<ReopenPattern[]>("/analytics/reopen-patterns", { params: { limit } })
      .then((r) => r.data),

  developerMetrics: (email: string) =>
    api.get<DeveloperMetrics>(`/analytics/developer/${email}`).then((r) => r.data),

  featureHealth: (name: string) =>
    api.get<FeatureHealthScore>(`/analytics/feature-health/${name}`).then((r) => r.data),
};

// ── RAG ──────────────────────────────────────────────────────────────────────

export const ragApi = {
  similarity: (text: string, nResults = 10, filterType?: string) =>
    api
      .post<SimilarityResult[]>("/rag/similarity", {
        text,
        n_results: nResults,
        filter_type: filterType || null,
      })
      .then((r) => r.data),

  duplicates: (summary: string, threshold = 0.85) =>
    api
      .post<DuplicateResult[]>("/rag/duplicates", { summary, threshold })
      .then((r) => r.data),

  stats: () => api.get("/rag/stats").then((r) => r.data),
};

// ── Agent ────────────────────────────────────────────────────────────────────

export const agentApi = {
  context: (featureName: string, jiraKey?: string) =>
    api
      .post<AgentContext>("/agent/review-context", {
        feature_name: featureName,
        jira_key: jiraKey || null,
      })
      .then((r) => r.data),

  risk: (featureName: string) =>
    api.post("/agent/risk-score", { feature_name: featureName }).then((r) => r.data),
};

// ── Workflows ────────────────────────────────────────────────────────────────

export const workflowApi = {
  trigger: (workflowType: string, params?: Record<string, unknown>) =>
    api
      .post<WorkflowRun>("/workflow/trigger", {
        workflow_type: workflowType,
        params,
      })
      .then((r) => r.data),

  status: (workflowId: string) =>
    api.get<WorkflowRun>(`/workflow/status/${workflowId}`).then((r) => r.data),

  recent: (limit = 20) =>
    api.get<WorkflowRun[]>("/workflow/recent", { params: { limit } }).then((r) => r.data),

  types: () =>
    api.get<{ workflow_types: string[] }>("/workflow/types").then((r) => r.data),
};

// ── Schedules ────────────────────────────────────────────────────────────────

export const scheduleApi = {
  list: (enabledOnly = false) =>
    api
      .get<WorkflowSchedule[]>("/schedules", { params: { enabled_only: enabledOnly } })
      .then((r) => r.data),

  get: (id: number) =>
    api.get<WorkflowSchedule>(`/schedules/${id}`).then((r) => r.data),

  create: (data: {
    name: string;
    workflow_type: string;
    cron_expression: string;
    params?: Record<string, unknown>;
    is_enabled?: boolean;
  }) => api.post<WorkflowSchedule>("/schedules", data).then((r) => r.data),

  update: (id: number, data: Partial<{ cron_expression: string; params: Record<string, unknown>; is_enabled: boolean }>) =>
    api.patch<WorkflowSchedule>(`/schedules/${id}`, data).then((r) => r.data),

  delete: (id: number) => api.delete(`/schedules/${id}`),

  enable: (id: number) =>
    api.post<WorkflowSchedule>(`/schedules/${id}/enable`).then((r) => r.data),

  disable: (id: number) =>
    api.post<WorkflowSchedule>(`/schedules/${id}/disable`).then((r) => r.data),

  trigger: (id: number) =>
    api.post(`/schedules/${id}/trigger`).then((r) => r.data),

  presets: () =>
    api.get<{ presets: Record<string, string> }>("/schedules/presets").then((r) => r.data),
};

export default api;
