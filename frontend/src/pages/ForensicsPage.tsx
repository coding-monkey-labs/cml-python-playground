import { useState } from "react";
import { jiraApi, agentApi } from "@/api/client";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge, StatusBadge } from "@/components/ui/Badge";
import { EmptyState, ErrorMessage } from "@/components/ui/Spinner";
import { Search, ArrowRight, Shield } from "lucide-react";
import type { JiraIssue, AgentContext } from "@/types";

export default function ForensicsPage() {
  const [jiraKey, setJiraKey] = useState("");
  const [issue, setIssue] = useState<JiraIssue | null>(null);
  const [context, setContext] = useState<AgentContext | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const investigate = async () => {
    if (!jiraKey.trim()) return;
    setIsLoading(true);
    setError("");
    setContext(null);
    try {
      const issueData = await jiraApi.get(jiraKey);
      setIssue(issueData);

      // Get agent context for the defect
      try {
        const ctx = await agentApi.context("", jiraKey);
        setContext(ctx);
      } catch {
        // Agent context may not be available
      }
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Issue not found"
      );
      setIssue(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Defect Forensics</h1>

      <Card>
        <p className="text-sm text-text-secondary mb-3">
          Investigate a defect: see its full chain from feature to epic to fix PRs, reopen history, and risk factors.
        </p>
        <div className="flex gap-3">
          <div className="flex-1">
            <Input
              placeholder="Enter Jira key (e.g. PROJ-123)"
              value={jiraKey}
              onChange={(e) => setJiraKey(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === "Enter" && investigate()}
            />
          </div>
          <Button onClick={investigate} isLoading={isLoading}>
            <Search size={16} className="mr-1" /> Investigate
          </Button>
        </div>
      </Card>

      {error && <ErrorMessage message={error} />}

      {issue && (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Issue Detail */}
          <Card>
            <CardHeader>
              <CardTitle>Issue Detail</CardTitle>
              <StatusBadge status={issue.status} />
            </CardHeader>
            <div className="space-y-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-sm font-bold">{issue.jira_key}</span>
                  <Badge variant={issue.issue_type === "defect" ? "danger" : "neutral"}>
                    {issue.issue_type}
                  </Badge>
                </div>
                <h3 className="text-lg font-semibold">{issue.summary}</h3>
              </div>

              {issue.description && (
                <p className="text-sm text-text-secondary line-clamp-4">
                  {issue.description}
                </p>
              )}

              <div className="grid grid-cols-2 gap-3 text-sm">
                <MetricItem label="Priority" value={issue.priority || "None"} />
                <MetricItem label="Severity" value={issue.severity || "None"} />
                <MetricItem label="Assignee" value={issue.assignee_email || "Unassigned"} />
                <MetricItem label="Reporter" value={issue.reporter_email || "Unknown"} />
                <MetricItem label="Epic" value={issue.epic_key || "None"} />
                <MetricItem label="Parent" value={issue.parent_key || "None"} />
              </div>

              {/* Reopen History */}
              {issue.reopen_count > 0 && (
                <div className="rounded-lg bg-amber-50 border border-amber-200 p-3">
                  <p className="text-sm font-medium text-amber-800">
                    Reopened {issue.reopen_count} time{issue.reopen_count > 1 ? "s" : ""}
                  </p>
                  {issue.resolution_time_hours && (
                    <p className="text-xs text-amber-700">
                      Avg resolution: {issue.resolution_time_hours.toFixed(1)}h
                    </p>
                  )}
                </div>
              )}
            </div>
          </Card>

          {/* Agent Context / Investigation */}
          <Card>
            <CardHeader>
              <CardTitle>
                <Shield size={16} className="inline mr-1" />
                Investigation Context
              </CardTitle>
            </CardHeader>
            {context ? (
              <div className="space-y-4">
                {context.risk_factors.length > 0 && (
                  <div>
                    <p className="text-xs text-text-muted mb-2 font-semibold uppercase">Risk Factors</p>
                    <div className="space-y-1">
                      {context.risk_factors.map((f, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm">
                          <ArrowRight size={12} className="text-danger shrink-0" />
                          <span>{f}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {context.related_defects.length > 0 && (
                  <div>
                    <p className="text-xs text-text-muted mb-2 font-semibold uppercase">Related Defects</p>
                    <div className="flex flex-wrap gap-1">
                      {context.related_defects.map((d) => (
                        <Badge key={d} variant="danger">{d}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                {context.recent_prs.length > 0 && (
                  <div>
                    <p className="text-xs text-text-muted mb-2 font-semibold uppercase">Related PRs</p>
                    <div className="flex flex-wrap gap-1">
                      {context.recent_prs.map((pr) => (
                        <Badge key={pr} variant="info">{pr}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                {context.feature_name && (
                  <div>
                    <p className="text-xs text-text-muted mb-1 font-semibold uppercase">Feature</p>
                    <Badge variant="info">{context.feature_name}</Badge>
                  </div>
                )}
              </div>
            ) : (
              <EmptyState message="No investigation context available. Ensure agent and RAG services are running." />
            )}
          </Card>
        </div>
      )}
    </div>
  );
}

function MetricItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-text-muted">{label}</p>
      <p className="font-medium truncate">{value}</p>
    </div>
  );
}
