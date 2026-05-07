import { useState } from "react";
import { useApi } from "@/hooks/useApi";
import { scheduleApi, workflowApi } from "@/api/client";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Select } from "@/components/ui/Input";
import { Badge, StatusBadge } from "@/components/ui/Badge";
import { Table, Thead, Th, Td, Tr } from "@/components/ui/Table";
import { PageLoader, ErrorMessage, EmptyState } from "@/components/ui/Spinner";
import { Plus, Play, Pause, Trash2, Clock } from "lucide-react";
import type { WorkflowSchedule } from "@/types";

export default function SchedulesPage() {
  const { data: schedules, isLoading, error, refetch } = useApi(() => scheduleApi.list());
  const { data: typesData } = useApi(() => workflowApi.types());
  const { data: presetsData } = useApi(() => scheduleApi.presets());
  const [showCreate, setShowCreate] = useState(false);

  if (isLoading) return <PageLoader />;
  if (error) return <ErrorMessage message={error} />;

  const types = typesData?.workflow_types || [];
  const presets = presetsData?.presets || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Scheduled Workflows</h1>
        <div className="flex gap-2">
          <Button onClick={() => setShowCreate(!showCreate)}>
            <Plus size={14} className="mr-1" /> New Schedule
          </Button>
          <Button variant="secondary" onClick={refetch}>
            Refresh
          </Button>
        </div>
      </div>

      {showCreate && (
        <CreateScheduleForm
          types={types}
          presets={presets}
          onCreated={() => { setShowCreate(false); refetch(); }}
          onCancel={() => setShowCreate(false)}
        />
      )}

      <Card padding={false}>
        <div className="p-4 border-b border-border">
          <CardTitle>All Schedules</CardTitle>
        </div>
        {!schedules || schedules.length === 0 ? (
          <EmptyState message="No schedules configured yet" />
        ) : (
          <Table>
            <Thead>
              <tr>
                <Th>Name</Th>
                <Th>Workflow</Th>
                <Th>Cron</Th>
                <Th>Status</Th>
                <Th>Last Run</Th>
                <Th>Actions</Th>
              </tr>
            </Thead>
            <tbody>
              {schedules.map((s) => (
                <ScheduleRow key={s.id} schedule={s} onAction={refetch} />
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </div>
  );
}

function ScheduleRow({
  schedule,
  onAction,
}: {
  schedule: WorkflowSchedule;
  onAction: () => void;
}) {
  const [loading, setLoading] = useState("");

  const action = async (fn: () => Promise<unknown>, name: string) => {
    setLoading(name);
    try {
      await fn();
      onAction();
    } catch {
      // ignore
    } finally {
      setLoading("");
    }
  };

  return (
    <Tr>
      <Td className="font-medium">{schedule.name}</Td>
      <Td><Badge>{schedule.workflow_type}</Badge></Td>
      <Td>
        <code className="rounded bg-surface-secondary px-2 py-0.5 text-xs">
          {schedule.cron_expression}
        </code>
      </Td>
      <Td>
        {schedule.is_enabled ? (
          <Badge variant="success">Enabled</Badge>
        ) : (
          <Badge variant="neutral">Disabled</Badge>
        )}
      </Td>
      <Td className="text-xs text-text-muted">
        {schedule.last_run_at ? new Date(schedule.last_run_at).toLocaleString() : "Never"}
      </Td>
      <Td>
        <div className="flex gap-1">
          {schedule.is_enabled ? (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => action(() => scheduleApi.disable(schedule.id), "disable")}
              isLoading={loading === "disable"}
              title="Disable"
            >
              <Pause size={14} />
            </Button>
          ) : (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => action(() => scheduleApi.enable(schedule.id), "enable")}
              isLoading={loading === "enable"}
              title="Enable"
            >
              <Play size={14} />
            </Button>
          )}
          <Button
            size="sm"
            variant="ghost"
            onClick={() => action(() => scheduleApi.trigger(schedule.id), "trigger")}
            isLoading={loading === "trigger"}
            title="Trigger now"
          >
            <Clock size={14} />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => action(() => scheduleApi.delete(schedule.id), "delete")}
            isLoading={loading === "delete"}
            title="Delete"
          >
            <Trash2 size={14} className="text-danger" />
          </Button>
        </div>
      </Td>
    </Tr>
  );
}

function CreateScheduleForm({
  types,
  presets,
  onCreated,
  onCancel,
}: {
  types: string[];
  presets: Record<string, string>;
  onCreated: () => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState("");
  const [workflowType, setWorkflowType] = useState(types[0] || "");
  const [cronExpression, setCronExpression] = useState("daily_2am");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleCreate = async () => {
    if (!name.trim() || !workflowType) return;
    setIsLoading(true);
    setError("");
    try {
      await scheduleApi.create({
        name,
        workflow_type: workflowType,
        cron_expression: cronExpression,
      });
      onCreated();
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Failed to create schedule"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create Schedule</CardTitle>
      </CardHeader>
      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 mb-4">{error}</div>
      )}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Input
          label="Schedule Name"
          placeholder="nightly-jira-sync"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <Select
          label="Workflow Type"
          options={types.map((t) => ({ value: t, label: t }))}
          value={workflowType}
          onChange={(e) => setWorkflowType(e.target.value)}
        />
        <Select
          label="Cron Schedule"
          options={[
            ...Object.entries(presets).map(([key, cron]) => ({
              value: key,
              label: `${key} (${cron})`,
            })),
            { value: "custom", label: "Custom expression" },
          ]}
          value={Object.keys(presets).includes(cronExpression) ? cronExpression : "custom"}
          onChange={(e) => setCronExpression(e.target.value)}
        />
        {!Object.keys(presets).includes(cronExpression) && (
          <Input
            label="Custom Cron"
            placeholder="0 */6 * * *"
            value={cronExpression}
            onChange={(e) => setCronExpression(e.target.value)}
          />
        )}
      </div>
      <div className="mt-4 flex gap-2">
        <Button onClick={handleCreate} isLoading={isLoading}>
          Create
        </Button>
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </Card>
  );
}
