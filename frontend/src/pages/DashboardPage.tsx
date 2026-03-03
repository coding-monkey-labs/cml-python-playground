import { useAuth } from "@/context/AuthContext";
import { useApi } from "@/hooks/useApi";
import { dashboardApi } from "@/api/client";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge, StatusBadge } from "@/components/ui/Badge";
import { PageLoader, ErrorMessage, EmptyState } from "@/components/ui/Spinner";
import { Table, Thead, Th, Td, Tr } from "@/components/ui/Table";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  GitBranch,
  Bug,
  GitPullRequest,
  AlertTriangle,
  Workflow,
  Calendar,
} from "lucide-react";
import type { ActivityItem } from "@/types";

export default function DashboardPage() {
  const { isAdmin } = useAuth();
  const { data: summary, isLoading, error } = useApi(() => dashboardApi.summary());
  const { data: trends } = useApi(() => dashboardApi.trends());
  const { data: activity } = useApi(() => dashboardApi.activity(10));

  if (isLoading) return <PageLoader />;
  if (error) return <ErrorMessage message={error} />;
  if (!summary) return null;

  const { entity_counts: ec, workflow_summary: ws } = summary;

  const trendData =
    trends?.defects_created.map((d, i) => ({
      period: d.period,
      Created: d.count,
      Reopened: trends.reopen_counts[i]?.count || 0,
    })) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <StatusBadge status={summary.system_health} />
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
        <StatCard icon={<GitBranch size={20} />} label="Features" value={ec.features} />
        <StatCard icon={<Bug size={20} />} label="Total Defects" value={ec.defect_count} />
        <StatCard
          icon={<AlertTriangle size={20} />}
          label="Open Defects"
          value={ec.open_defects}
          accent="danger"
        />
        <StatCard icon={<GitPullRequest size={20} />} label="Pull Requests" value={ec.pull_requests} />
        {isAdmin && (
          <>
            <StatCard icon={<Workflow size={20} />} label="Workflow Runs" value={ws.total_runs} />
            <StatCard icon={<Calendar size={20} />} label="Active Schedules" value={ws.active_schedules} />
          </>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Hotspots */}
        <Card>
          <CardHeader>
            <CardTitle>Top Hotspots</CardTitle>
          </CardHeader>
          {summary.top_hotspots.length === 0 ? (
            <EmptyState message="No hotspots detected" />
          ) : (
            <Table>
              <Thead>
                <tr>
                  <Th>Feature</Th>
                  <Th>Defects</Th>
                  <Th>Health</Th>
                </tr>
              </Thead>
              <tbody>
                {summary.top_hotspots.map((h) => (
                  <Tr key={h.feature}>
                    <Td className="font-medium">{h.feature}</Td>
                    <Td>{h.defect_count}</Td>
                    <Td>
                      <HealthBar score={h.health_score} />
                    </Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card>

        {/* Recent Defects */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Defects</CardTitle>
          </CardHeader>
          {summary.recent_defects.length === 0 ? (
            <EmptyState message="No defects found" />
          ) : (
            <Table>
              <Thead>
                <tr>
                  <Th>Key</Th>
                  <Th>Summary</Th>
                  <Th>Status</Th>
                  <Th>Priority</Th>
                </tr>
              </Thead>
              <tbody>
                {summary.recent_defects.map((d) => (
                  <Tr key={d.jira_key}>
                    <Td className="font-mono text-xs">{d.jira_key}</Td>
                    <Td className="max-w-[200px] truncate">{d.summary}</Td>
                    <Td>{d.status && <StatusBadge status={d.status} />}</Td>
                    <Td>{d.priority || "-"}</Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Trend Chart */}
        {trendData.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Defect Trends</CardTitle>
            </CardHeader>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="period" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Legend />
                <Bar dataKey="Created" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Reopened" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        )}

        {/* Activity Feed */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          {!activity || activity.length === 0 ? (
            <EmptyState message="No recent activity" />
          ) : (
            <div className="space-y-3 max-h-[250px] overflow-y-auto">
              {activity.map((item, i) => (
                <ActivityRow key={i} item={item} />
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  accent?: "danger" | "success";
}) {
  return (
    <Card className="flex items-center gap-3">
      <div className="text-text-muted">{icon}</div>
      <div>
        <p className={`text-xl font-bold ${accent === "danger" ? "text-danger" : ""}`}>
          {value.toLocaleString()}
        </p>
        <p className="text-xs text-text-muted">{label}</p>
      </div>
    </Card>
  );
}

function HealthBar({ score }: { score: number }) {
  const color =
    score >= 70 ? "bg-green-500" : score >= 40 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-16 rounded-full bg-gray-200">
        <div
          className={`h-2 rounded-full ${color}`}
          style={{ width: `${Math.max(0, Math.min(100, score))}%` }}
        />
      </div>
      <span className="text-xs text-text-muted">{score.toFixed(0)}</span>
    </div>
  );
}

function ActivityRow({ item }: { item: ActivityItem }) {
  const typeColors: Record<string, string> = {
    jira_defect: "bg-red-100 text-red-700",
    jira_story: "bg-blue-100 text-blue-700",
    jira_task: "bg-gray-100 text-gray-700",
    jira_epic: "bg-purple-100 text-purple-700",
    pr_merged: "bg-green-100 text-green-700",
    pr_open: "bg-blue-100 text-blue-700",
    workflow_completed: "bg-green-100 text-green-700",
    workflow_failed: "bg-red-100 text-red-700",
    workflow_running: "bg-blue-100 text-blue-700",
  };

  return (
    <div className="flex items-start gap-3 text-sm">
      <Badge
        className={typeColors[item.type] || "bg-gray-100 text-gray-700"}
      >
        {item.type.split("_")[0]}
      </Badge>
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium">{item.title}</p>
        {item.detail && (
          <p className="text-xs text-text-muted truncate">{item.detail}</p>
        )}
      </div>
      {item.timestamp && (
        <span className="shrink-0 text-xs text-text-muted">
          {new Date(item.timestamp).toLocaleDateString()}
        </span>
      )}
    </div>
  );
}
