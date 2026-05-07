import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useApi } from "@/hooks/useApi";
import { analyticsApi } from "@/api/client";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { PageLoader, ErrorMessage, EmptyState } from "@/components/ui/Spinner";
import { User, BarChart3, RefreshCw, Bug, CheckCircle } from "lucide-react";
import type { DeveloperMetrics } from "@/types";

export default function ProfilePage() {
  const { user } = useAuth();
  const [email, setEmail] = useState(user?.email || "");
  const [metrics, setMetrics] = useState<DeveloperMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const loadMetrics = async () => {
    if (!email.trim()) return;
    setIsLoading(true);
    setError("");
    try {
      const data = await analyticsApi.developerMetrics(email);
      setMetrics(data);
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Failed to load metrics"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Developer Profile</h1>

      <Card>
        <div className="flex gap-3">
          <div className="flex-1">
            <Input
              placeholder="Developer email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && loadMetrics()}
            />
          </div>
          <Button onClick={loadMetrics} isLoading={isLoading}>
            <BarChart3 size={16} className="mr-1" /> Load Profile
          </Button>
        </div>
      </Card>

      {error && <ErrorMessage message={error} />}

      {metrics && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            icon={<Bug size={24} />}
            label="Total Issues"
            value={metrics.total_issues.toString()}
            color="text-primary-600"
          />
          <StatCard
            icon={<RefreshCw size={24} />}
            label="Reopen Rate"
            value={`${(metrics.reopen_rate * 100).toFixed(1)}%`}
            color={metrics.reopen_rate > 0.2 ? "text-danger" : "text-success"}
          />
          <StatCard
            icon={<CheckCircle size={24} />}
            label="Fix Completeness"
            value={`${(metrics.fix_completeness * 100).toFixed(1)}%`}
            color={metrics.fix_completeness >= 0.8 ? "text-success" : "text-warning"}
          />
          <StatCard
            icon={<BarChart3 size={24} />}
            label="Avg Resolution"
            value={
              metrics.avg_resolution_hours
                ? `${metrics.avg_resolution_hours.toFixed(1)}h`
                : "N/A"
            }
            color="text-text-primary"
          />
        </div>
      )}

      {metrics && (
        <Card>
          <CardHeader>
            <CardTitle>Profile Summary</CardTitle>
          </CardHeader>
          <div className="flex items-center gap-4 mb-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-100">
              <User size={24} className="text-primary-600" />
            </div>
            <div>
              <h3 className="font-semibold">{metrics.email}</h3>
              <p className="text-sm text-text-muted">
                {metrics.total_issues} issues tracked
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <ProgressBar
              label="Fix Completeness"
              value={metrics.fix_completeness * 100}
              color={metrics.fix_completeness >= 0.8 ? "bg-green-500" : "bg-amber-500"}
            />
            <ProgressBar
              label="Reopen Rate (lower is better)"
              value={metrics.reopen_rate * 100}
              color={metrics.reopen_rate <= 0.1 ? "bg-green-500" : "bg-red-500"}
            />
          </div>
        </Card>
      )}
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <Card className="flex items-center gap-4">
      <div className={color}>{icon}</div>
      <div>
        <p className="text-xl font-bold">{value}</p>
        <p className="text-xs text-text-muted">{label}</p>
      </div>
    </Card>
  );
}

function ProgressBar({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-text-secondary">{label}</span>
        <span className="font-medium">{value.toFixed(1)}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-gray-200">
        <div
          className={`h-2 rounded-full ${color}`}
          style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        />
      </div>
    </div>
  );
}
