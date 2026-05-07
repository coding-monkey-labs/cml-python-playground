import { useState } from "react";
import { useApi } from "@/hooks/useApi";
import { featuresApi, analyticsApi } from "@/api/client";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { PageLoader, ErrorMessage, EmptyState } from "@/components/ui/Spinner";
import { Table, Thead, Th, Td, Tr } from "@/components/ui/Table";
import { ChevronRight, ChevronDown, GitBranch } from "lucide-react";
import type { Feature, FeatureHealthScore } from "@/types";

export default function FeaturesPage() {
  const { data: features, isLoading, error } = useApi(() => featuresApi.list());
  const [selectedFeature, setSelectedFeature] = useState<string | null>(null);
  const [healthData, setHealthData] = useState<FeatureHealthScore | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(false);

  if (isLoading) return <PageLoader />;
  if (error) return <ErrorMessage message={error} />;
  if (!features) return null;

  // Build tree structure
  const rootFeatures = features.filter((f) => !f.parent_id);
  const childMap = new Map<number, Feature[]>();
  features.forEach((f) => {
    if (f.parent_id) {
      const children = childMap.get(f.parent_id) || [];
      children.push(f);
      childMap.set(f.parent_id, children);
    }
  });

  const loadHealth = async (name: string) => {
    setSelectedFeature(name);
    setLoadingHealth(true);
    try {
      const data = await analyticsApi.featureHealth(name);
      setHealthData(data);
    } catch {
      setHealthData(null);
    } finally {
      setLoadingHealth(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Feature Explorer</h1>
        <Badge variant="info">{features.length} features</Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Feature Tree */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Feature Hierarchy</CardTitle>
            </CardHeader>

            {/* Health Heatmap */}
            {features.length > 0 && (
              <div className="mb-4">
                <p className="text-xs text-text-muted mb-2 uppercase tracking-wide font-semibold">Health Heatmap</p>
                <div className="flex flex-wrap gap-1">
                  {features
                    .filter((f) => f.defect_count > 0)
                    .sort((a, b) => a.health_score - b.health_score)
                    .map((f) => (
                      <button
                        key={f.id}
                        onClick={() => loadHealth(f.name)}
                        title={`${f.name}: ${f.health_score.toFixed(0)} health, ${f.defect_count} defects`}
                        className={`h-8 rounded px-2 text-[10px] font-medium text-white transition-transform hover:scale-110 ${
                          f.health_score >= 70
                            ? "bg-green-500"
                            : f.health_score >= 40
                            ? "bg-amber-500"
                            : "bg-red-500"
                        }`}
                      >
                        {f.name}
                      </button>
                    ))}
                </div>
              </div>
            )}

            {rootFeatures.length === 0 ? (
              <EmptyState message="No features indexed yet. Run the feature_graph_build workflow." />
            ) : (
              <div className="space-y-1">
                {rootFeatures.map((f) => (
                  <FeatureNode
                    key={f.id}
                    feature={f}
                    childMap={childMap}
                    depth={0}
                    onSelect={loadHealth}
                    selected={selectedFeature}
                  />
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Detail Panel */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Feature Detail</CardTitle>
            </CardHeader>
            {!selectedFeature ? (
              <EmptyState message="Select a feature to view details" />
            ) : loadingHealth ? (
              <p className="text-sm text-text-muted">Loading...</p>
            ) : healthData ? (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">{healthData.feature_name}</h3>
                <MetricRow label="Health Score" value={`${healthData.health_score.toFixed(1)}/100`} />
                <MetricRow label="Defect Density" value={healthData.defect_density.toFixed(4)} />
                <MetricRow label="Volatility" value={healthData.volatility_score.toFixed(4)} />
                <MetricRow
                  label="Regression Likelihood"
                  value={`${(healthData.regression_likelihood * 100).toFixed(1)}%`}
                />

                {/* Health gauge */}
                <div className="pt-2">
                  <div className="h-3 w-full rounded-full bg-gray-200">
                    <div
                      className={`h-3 rounded-full transition-all ${
                        healthData.health_score >= 70
                          ? "bg-green-500"
                          : healthData.health_score >= 40
                          ? "bg-amber-500"
                          : "bg-red-500"
                      }`}
                      style={{ width: `${Math.max(0, Math.min(100, healthData.health_score))}%` }}
                    />
                  </div>
                </div>
              </div>
            ) : (
              <EmptyState message="No health data available" />
            )}
          </Card>
        </div>
      </div>

      {/* Features Table */}
      <Card padding={false}>
        <div className="p-4 border-b border-border">
          <CardTitle>All Features</CardTitle>
        </div>
        <Table>
          <Thead>
            <tr>
              <Th>Name</Th>
              <Th>Path</Th>
              <Th>Defects</Th>
              <Th>Health</Th>
            </tr>
          </Thead>
          <tbody>
            {features
              .sort((a, b) => b.defect_count - a.defect_count)
              .slice(0, 50)
              .map((f) => (
                <Tr key={f.id} onClick={() => loadHealth(f.name)}>
                  <Td className="font-medium">{f.name}</Td>
                  <Td className="text-xs text-text-muted font-mono">
                    {f.file_path || "-"}
                  </Td>
                  <Td>
                    {f.defect_count > 0 ? (
                      <Badge variant="danger">{f.defect_count}</Badge>
                    ) : (
                      "0"
                    )}
                  </Td>
                  <Td>
                    <HealthPill score={f.health_score} />
                  </Td>
                </Tr>
              ))}
          </tbody>
        </Table>
      </Card>
    </div>
  );
}

function FeatureNode({
  feature,
  childMap,
  depth,
  onSelect,
  selected,
}: {
  feature: Feature;
  childMap: Map<number, Feature[]>;
  depth: number;
  onSelect: (name: string) => void;
  selected: string | null;
}) {
  const [open, setOpen] = useState(depth < 1);
  const children = childMap.get(feature.id) || [];
  const hasChildren = children.length > 0;

  return (
    <div>
      <button
        className={`flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-sm hover:bg-surface-hover ${
          selected === feature.name ? "bg-primary-50 text-primary-700" : ""
        }`}
        style={{ paddingLeft: `${depth * 20 + 8}px` }}
        onClick={() => {
          if (hasChildren) setOpen(!open);
          onSelect(feature.name);
        }}
      >
        {hasChildren ? (
          open ? <ChevronDown size={14} /> : <ChevronRight size={14} />
        ) : (
          <GitBranch size={14} className="text-text-muted" />
        )}
        <span className="flex-1 text-left truncate">{feature.name}</span>
        {feature.defect_count > 0 && (
          <Badge variant="danger">{feature.defect_count}</Badge>
        )}
      </button>
      {open &&
        children.map((child) => (
          <FeatureNode
            key={child.id}
            feature={child}
            childMap={childMap}
            depth={depth + 1}
            onSelect={onSelect}
            selected={selected}
          />
        ))}
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-text-secondary">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

function HealthPill({ score }: { score: number }) {
  const color =
    score >= 70
      ? "text-green-700 bg-green-100"
      : score >= 40
      ? "text-amber-700 bg-amber-100"
      : "text-red-700 bg-red-100";
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${color}`}>
      {score.toFixed(0)}
    </span>
  );
}
