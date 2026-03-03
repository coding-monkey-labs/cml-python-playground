import { useApi } from "@/hooks/useApi";
import { dashboardApi } from "@/api/client";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge, StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Table, Thead, Th, Td, Tr } from "@/components/ui/Table";
import { PageLoader, ErrorMessage } from "@/components/ui/Spinner";
import { HeartPulse, Activity, AlertCircle, CheckCircle } from "lucide-react";

export default function HealthPage() {
  const { data: health, isLoading, error, refetch } = useApi(() =>
    dashboardApi.systemHealth()
  );

  if (isLoading) return <PageLoader />;
  if (error) return <ErrorMessage message={error} />;
  if (!health) return null;

  const overallColor =
    health.overall === "healthy"
      ? "text-green-600"
      : health.overall === "degraded"
      ? "text-amber-600"
      : "text-red-600";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">System Health</h1>
        <Button variant="secondary" onClick={refetch}>
          Refresh
        </Button>
      </div>

      {/* Overall Status */}
      <Card>
        <div className="flex items-center gap-4">
          <div className={`${overallColor}`}>
            <HeartPulse size={40} />
          </div>
          <div>
            <h2 className={`text-3xl font-bold capitalize ${overallColor}`}>
              {health.overall}
            </h2>
            <p className="text-sm text-text-secondary">System status</p>
          </div>
        </div>
      </Card>

      <div className="grid gap-6 md:grid-cols-3">
        {/* 24h Workflow Stats */}
        <Card className="flex items-center gap-4">
          <Activity size={32} className="text-primary-500" />
          <div>
            <p className="text-2xl font-bold">{health.total_workflow_runs_24h}</p>
            <p className="text-xs text-text-muted">Workflow runs (24h)</p>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <AlertCircle size={32} className="text-danger" />
          <div>
            <p className="text-2xl font-bold text-danger">
              {health.failed_workflow_runs_24h}
            </p>
            <p className="text-xs text-text-muted">Failed runs (24h)</p>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <CheckCircle size={32} className="text-success" />
          <div>
            <p className="text-2xl font-bold">
              {health.total_workflow_runs_24h - health.failed_workflow_runs_24h}
            </p>
            <p className="text-xs text-text-muted">Successful runs (24h)</p>
          </div>
        </Card>
      </div>

      {/* Service Status */}
      <Card padding={false}>
        <div className="p-4 border-b border-border">
          <CardTitle>Service Status</CardTitle>
        </div>
        <Table>
          <Thead>
            <tr>
              <Th>Service</Th>
              <Th>Status</Th>
              <Th>Latency</Th>
            </tr>
          </Thead>
          <tbody>
            {health.services.map((svc) => (
              <Tr key={svc.name}>
                <Td className="font-medium capitalize">{svc.name}</Td>
                <Td><StatusBadge status={svc.status} /></Td>
                <Td className="text-text-muted">
                  {svc.latency_ms ? `${svc.latency_ms.toFixed(1)}ms` : "N/A"}
                </Td>
              </Tr>
            ))}
          </tbody>
        </Table>
      </Card>

      {health.database_size_mb && (
        <Card>
          <CardHeader>
            <CardTitle>Database</CardTitle>
          </CardHeader>
          <p className="text-sm">
            Size: <span className="font-mono font-medium">{health.database_size_mb.toFixed(1)} MB</span>
          </p>
        </Card>
      )}
    </div>
  );
}
