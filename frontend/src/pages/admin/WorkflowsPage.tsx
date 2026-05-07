import { useState } from "react";
import { useApi } from "@/hooks/useApi";
import { workflowApi } from "@/api/client";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Input";
import { StatusBadge } from "@/components/ui/Badge";
import { Table, Thead, Th, Td, Tr } from "@/components/ui/Table";
import { PageLoader, ErrorMessage, EmptyState } from "@/components/ui/Spinner";
import { Play } from "lucide-react";

export default function WorkflowsPage() {
  const { data: runs, isLoading, error, refetch } = useApi(() => workflowApi.recent(50));
  const { data: typesData } = useApi(() => workflowApi.types());
  const [selectedType, setSelectedType] = useState("");
  const [triggering, setTriggering] = useState(false);

  const triggerWorkflow = async () => {
    if (!selectedType) return;
    setTriggering(true);
    try {
      await workflowApi.trigger(selectedType);
      refetch();
    } catch {
      // ignore
    } finally {
      setTriggering(false);
    }
  };

  if (isLoading) return <PageLoader />;
  if (error) return <ErrorMessage message={error} />;

  const types = typesData?.workflow_types || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Workflows</h1>
        <div className="flex gap-2">
          <Select
            options={[
              { value: "", label: "Select workflow..." },
              ...types.map((t) => ({ value: t, label: t })),
            ]}
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="w-56"
          />
          <Button
            onClick={triggerWorkflow}
            isLoading={triggering}
            disabled={!selectedType}
          >
            <Play size={14} className="mr-1" /> Trigger
          </Button>
          <Button variant="secondary" onClick={refetch}>
            Refresh
          </Button>
        </div>
      </div>

      <Card padding={false}>
        <div className="p-4 border-b border-border">
          <CardTitle>Recent Runs</CardTitle>
        </div>
        {!runs || runs.length === 0 ? (
          <EmptyState message="No workflow runs yet" />
        ) : (
          <Table>
            <Thead>
              <tr>
                <Th>Workflow ID</Th>
                <Th>Type</Th>
                <Th>Status</Th>
                <Th>Started</Th>
                <Th>Completed</Th>
                <Th>Error</Th>
              </tr>
            </Thead>
            <tbody>
              {runs.map((run) => (
                <Tr key={run.id}>
                  <Td className="font-mono text-xs">{run.workflow_id}</Td>
                  <Td>{run.workflow_type}</Td>
                  <Td><StatusBadge status={run.status} /></Td>
                  <Td className="text-xs text-text-muted">
                    {run.started_at ? new Date(run.started_at).toLocaleString() : "-"}
                  </Td>
                  <Td className="text-xs text-text-muted">
                    {run.completed_at ? new Date(run.completed_at).toLocaleString() : "-"}
                  </Td>
                  <Td className="max-w-[200px] truncate text-xs text-danger">
                    {run.error_message || ""}
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </div>
  );
}
