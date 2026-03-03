// ── Auth ──────────────────────────────────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: "developer" | "admin";
  is_active: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

// ── Features ─────────────────────────────────────────────────────────────────

export interface Feature {
  id: number;
  name: string;
  description: string | null;
  file_path: string | null;
  parent_id: number | null;
  defect_count: number;
  health_score: number;
}

export interface FeatureMetrics {
  feature_name: string;
  defect_count: number;
  reopen_count: number;
  defect_density: number;
  health_score: number;
}

// ── Jira ─────────────────────────────────────────────────────────────────────

export interface JiraIssue {
  id: number;
  jira_key: string;
  issue_type: string;
  summary: string;
  description: string | null;
  status: string;
  priority: string | null;
  severity: string | null;
  assignee_email: string | null;
  reporter_email: string | null;
  parent_key: string | null;
  epic_key: string | null;
  reopen_count: number;
  resolution_time_hours: number | null;
  labels: string | null;
  components: string | null;
}

// ── Pull Requests ────────────────────────────────────────────────────────────

export interface PullRequest {
  id: number;
  pr_number: number;
  repo: string;
  title: string;
  description: string | null;
  status: string;
  author_email: string | null;
  author_login: string | null;
  files_changed: number;
  additions: number;
  deletions: number;
  merged_at: string | null;
}

export interface PRImpact {
  pr_number: number;
  repo: string;
  risk_score: number;
  related_defects: number;
  affected_features: string[];
}

// ── Analytics ────────────────────────────────────────────────────────────────

export interface HotspotFeature {
  feature: string;
  defect_count: number;
  total_weight: number;
}

export interface ReopenPattern {
  defect: string;
  reopened_from: string;
  summary: string;
}

export interface DeveloperMetrics {
  email: string;
  total_issues: number;
  avg_resolution_hours: number | null;
  reopen_rate: number;
  fix_completeness: number;
}

export interface FeatureHealthScore {
  feature_name: string;
  health_score: number;
  defect_density: number;
  volatility_score: number;
  regression_likelihood: number;
}

// ── Dashboard ────────────────────────────────────────────────────────────────

export interface EntityCounts {
  features: number;
  jira_issues: number;
  pull_requests: number;
  defect_count: number;
  open_defects: number;
}

export interface WorkflowSummary {
  total_runs: number;
  running: number;
  completed: number;
  failed: number;
  active_schedules: number;
}

export interface DashboardSummaryResponse {
  entity_counts: EntityCounts;
  workflow_summary: WorkflowSummary;
  top_hotspots: Array<{
    feature: string;
    defect_count: number;
    health_score: number;
  }>;
  recent_defects: Array<{
    jira_key: string;
    summary: string;
    status: string | null;
    priority: string | null;
  }>;
  system_health: string;
}

export interface TrendPoint {
  period: string;
  count: number;
}

export interface DefectTrends {
  defects_created: TrendPoint[];
  defects_resolved: TrendPoint[];
  reopen_counts: TrendPoint[];
}

export interface ActivityItem {
  type: string;
  title: string;
  detail: string | null;
  timestamp: string | null;
}

export interface ServiceStatus {
  name: string;
  status: string;
  latency_ms: number | null;
}

export interface SystemHealth {
  overall: string;
  services: ServiceStatus[];
  database_size_mb: number | null;
  total_workflow_runs_24h: number;
  failed_workflow_runs_24h: number;
}

// ── Workflows ────────────────────────────────────────────────────────────────

export interface WorkflowRun {
  id: number;
  workflow_type: string;
  workflow_id: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

export interface WorkflowSchedule {
  id: number;
  name: string;
  workflow_type: string;
  cron_expression: string;
  params: Record<string, unknown> | null;
  is_enabled: boolean;
  temporal_schedule_id: string | null;
  last_run_at: string | null;
  next_run_at: string | null;
  created_at: string | null;
}

// ── RAG ──────────────────────────────────────────────────────────────────────

export interface SimilarityResult {
  jira_key: string;
  summary: string;
  score: number;
  issue_type: string;
}

export interface DuplicateResult {
  jira_key: string;
  summary: string;
  similarity: number;
  is_duplicate: boolean;
}

// ── Agent ────────────────────────────────────────────────────────────────────

export interface AgentContext {
  feature_name: string;
  jira_key: string | null;
  related_defects: string[];
  recent_prs: string[];
  risk_factors: string[];
}

// ── Graph ────────────────────────────────────────────────────────────────────

export interface GraphNode {
  id: string;
  label: string;
  type: "feature" | "defect" | "pr" | "epic" | "story";
  data?: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  label?: string;
}
