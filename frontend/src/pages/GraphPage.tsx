import { useCallback, useEffect, useRef, useState } from "react";
import CytoscapeComponent from "react-cytoscapejs";
import type cytoscape from "cytoscape";
import { useApi } from "@/hooks/useApi";
import { featuresApi, jiraApi } from "@/api/client";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Select } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { PageLoader, ErrorMessage, EmptyState } from "@/components/ui/Spinner";
import { ZoomIn, ZoomOut, Maximize2, RefreshCw } from "lucide-react";
import type { Feature } from "@/types";

const NODE_COLORS: Record<string, string> = {
  feature: "#3b82f6",
  defect: "#ef4444",
  story: "#8b5cf6",
  task: "#6b7280",
  epic: "#f59e0b",
  pr: "#22c55e",
};

const cyStylesheet: cytoscape.StylesheetStyle[] = [
  {
    selector: "node",
    style: {
      label: "data(label)",
      "background-color": "data(color)",
      color: "#374151",
      "font-size": "10px",
      "text-valign": "bottom",
      "text-margin-y": 6,
      width: "data(size)",
      height: "data(size)",
    },
  },
  {
    selector: "edge",
    style: {
      "line-color": "#d1d5db",
      width: 1,
      "curve-style": "bezier",
      "target-arrow-shape": "triangle",
      "target-arrow-color": "#d1d5db",
      "arrow-scale": 0.6,
    },
  },
  {
    selector: "node:selected",
    style: {
      "border-width": 3,
      "border-color": "#1d4ed8",
    },
  },
];

export default function GraphPage() {
  const { data: features, isLoading, error } = useApi(() => featuresApi.list());
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [selectedNode, setSelectedNode] = useState<Record<string, string> | null>(null);
  const [jiraKey, setJiraKey] = useState("");
  const [subtreeData, setSubtreeData] = useState<cytoscape.ElementDefinition[]>([]);

  const buildElements = useCallback((): cytoscape.ElementDefinition[] => {
    if (!features) return [];
    const elements: cytoscape.ElementDefinition[] = [];

    features.forEach((f) => {
      const healthColor =
        f.health_score >= 70 ? NODE_COLORS.feature : f.health_score >= 40 ? NODE_COLORS.epic : NODE_COLORS.defect;
      elements.push({
        data: {
          id: `f-${f.id}`,
          label: f.name,
          color: healthColor,
          size: Math.max(20, Math.min(50, 20 + f.defect_count * 3)),
          nodeType: "feature",
        },
      });

      if (f.parent_id) {
        elements.push({
          data: {
            source: `f-${f.parent_id}`,
            target: `f-${f.id}`,
          },
        });
      }
    });

    return elements;
  }, [features]);

  const elements = subtreeData.length > 0 ? subtreeData : buildElements();

  const handleCyReady = (cy: cytoscape.Core) => {
    cyRef.current = cy;
    cy.on("tap", "node", (e) => {
      const data = e.target.data();
      setSelectedNode(data);
    });
    cy.on("tap", (e) => {
      if (e.target === cy) setSelectedNode(null);
    });
  };

  const loadSubtree = async () => {
    if (!jiraKey.trim()) return;
    try {
      const data = await jiraApi.subtree(jiraKey);
      const els: cytoscape.ElementDefinition[] = [];

      if (Array.isArray(data)) {
        data.forEach((item: Record<string, string>, i: number) => {
          els.push({
            data: {
              id: `j-${i}`,
              label: item.jira_key || item.name || `Node ${i}`,
              color: NODE_COLORS[item.issue_type] || NODE_COLORS.task,
              size: 30,
              nodeType: item.issue_type || "task",
            },
          });
          if (item.parent_key) {
            const parentIdx = data.findIndex((p: Record<string, string>) => p.jira_key === item.parent_key);
            if (parentIdx >= 0) {
              els.push({ data: { source: `j-${parentIdx}`, target: `j-${i}` } });
            }
          }
        });
      }
      setSubtreeData(els);
    } catch {
      // ignore
    }
  };

  if (isLoading) return <PageLoader />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Graph Explorer</h1>
        <div className="flex gap-2">
          <Input
            placeholder="Jira key (e.g. PROJ-100)"
            value={jiraKey}
            onChange={(e) => setJiraKey(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && loadSubtree()}
            className="w-48"
          />
          <Button size="sm" onClick={loadSubtree}>
            Load Subtree
          </Button>
          {subtreeData.length > 0 && (
            <Button size="sm" variant="secondary" onClick={() => setSubtreeData([])}>
              Show Features
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        <div className="lg:col-span-3">
          <Card padding={false} className="relative h-[600px]">
            {elements.length === 0 ? (
              <EmptyState message="No graph data. Run workflows to populate." />
            ) : (
              <>
                <CytoscapeComponent
                  elements={elements}
                  stylesheet={cyStylesheet}
                  layout={{ name: "cose", animate: false } as cytoscape.LayoutOptions}
                  className="h-full w-full"
                  cy={handleCyReady}
                />
                {/* Controls */}
                <div className="absolute top-3 right-3 flex flex-col gap-1">
                  <button
                    onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 1.2)}
                    className="rounded bg-white/90 p-1.5 shadow hover:bg-white"
                  >
                    <ZoomIn size={16} />
                  </button>
                  <button
                    onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 0.8)}
                    className="rounded bg-white/90 p-1.5 shadow hover:bg-white"
                  >
                    <ZoomOut size={16} />
                  </button>
                  <button
                    onClick={() => cyRef.current?.fit()}
                    className="rounded bg-white/90 p-1.5 shadow hover:bg-white"
                  >
                    <Maximize2 size={16} />
                  </button>
                  <button
                    onClick={() => cyRef.current?.layout({ name: "cose", animate: true } as cytoscape.LayoutOptions).run()}
                    className="rounded bg-white/90 p-1.5 shadow hover:bg-white"
                  >
                    <RefreshCw size={16} />
                  </button>
                </div>
              </>
            )}
          </Card>
        </div>

        {/* Node Detail */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Node Details</CardTitle>
            </CardHeader>
            {selectedNode ? (
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-text-muted">Label:</span>
                  <p className="font-medium">{selectedNode.label}</p>
                </div>
                <div>
                  <span className="text-text-muted">Type:</span>
                  <Badge className="ml-2">{selectedNode.nodeType || "unknown"}</Badge>
                </div>
                {selectedNode.size && (
                  <div>
                    <span className="text-text-muted">Size (defect weight):</span>
                    <p className="font-mono">{selectedNode.size}</p>
                  </div>
                )}
              </div>
            ) : (
              <EmptyState message="Click a node to view details" />
            )}
          </Card>

          {/* Legend */}
          <Card className="mt-4">
            <CardHeader>
              <CardTitle>Legend</CardTitle>
            </CardHeader>
            <div className="space-y-2">
              {Object.entries(NODE_COLORS).map(([type, color]) => (
                <div key={type} className="flex items-center gap-2 text-sm">
                  <div className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
                  <span className="capitalize">{type}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
