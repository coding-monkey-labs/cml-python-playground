import { useState } from "react";
import { prApi } from "@/api/client";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Select } from "@/components/ui/Input";
import { Badge, StatusBadge } from "@/components/ui/Badge";
import { Table, Thead, Th, Td, Tr } from "@/components/ui/Table";
import { EmptyState, ErrorMessage } from "@/components/ui/Spinner";
import type { PullRequest, PRImpact } from "@/types";

export default function PRPage() {
  const [repo, setRepo] = useState("");
  const [status, setStatus] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [results, setResults] = useState<PullRequest[]>([]);
  const [selectedPR, setSelectedPR] = useState<PullRequest | null>(null);
  const [impact, setImpact] = useState<PRImpact | null>(null);
  const [loadingImpact, setLoadingImpact] = useState(false);

  const handleSearch = async () => {
    if (!repo.trim()) return;
    setIsLoading(true);
    setError("");
    try {
      const prs = await prApi.search(repo, status || undefined);
      setResults(prs);
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Search failed");
    } finally {
      setIsLoading(false);
    }
  };

  const loadImpact = async (pr: PullRequest) => {
    setSelectedPR(pr);
    setLoadingImpact(true);
    try {
      const data = await prApi.impact(pr.repo, pr.pr_number);
      setImpact(data);
    } catch {
      setImpact(null);
    } finally {
      setLoadingImpact(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">PR Intelligence</h1>

      <Card>
        <div className="flex gap-3">
          <div className="flex-1">
            <Input
              placeholder="Repository (e.g. org/repo)"
              value={repo}
              onChange={(e) => setRepo(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
          </div>
          <Select
            options={[
              { value: "", label: "All Statuses" },
              { value: "open", label: "Open" },
              { value: "merged", label: "Merged" },
              { value: "closed", label: "Closed" },
            ]}
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="w-36"
          />
          <Button onClick={handleSearch} isLoading={isLoading}>
            Search
          </Button>
        </div>
      </Card>

      {error && <ErrorMessage message={error} />}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          {results.length > 0 && (
            <Card padding={false}>
              <div className="p-4 border-b border-border">
                <CardTitle>Pull Requests ({results.length})</CardTitle>
              </div>
              <Table>
                <Thead>
                  <tr>
                    <Th>#</Th>
                    <Th>Title</Th>
                    <Th>Status</Th>
                    <Th>Author</Th>
                    <Th>Changes</Th>
                  </tr>
                </Thead>
                <tbody>
                  {results.map((pr) => (
                    <Tr key={pr.id} onClick={() => loadImpact(pr)}>
                      <Td className="font-mono text-xs">{pr.pr_number}</Td>
                      <Td className="max-w-[300px] truncate font-medium">{pr.title}</Td>
                      <Td><StatusBadge status={pr.status} /></Td>
                      <Td className="text-xs">{pr.author_login || pr.author_email || "-"}</Td>
                      <Td>
                        <span className="text-xs">
                          <span className="text-green-600">+{pr.additions}</span>
                          {" / "}
                          <span className="text-red-600">-{pr.deletions}</span>
                          {" / "}
                          <span className="text-text-muted">{pr.files_changed} files</span>
                        </span>
                      </Td>
                    </Tr>
                  ))}
                </tbody>
              </Table>
            </Card>
          )}
          {!isLoading && results.length === 0 && repo && (
            <EmptyState message="No PRs found. Try a different repo." />
          )}
        </div>

        {/* Impact Panel */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Impact Analysis</CardTitle>
            </CardHeader>
            {!selectedPR ? (
              <EmptyState message="Click a PR to analyze impact" />
            ) : loadingImpact ? (
              <p className="text-sm text-text-muted">Analyzing...</p>
            ) : impact ? (
              <div className="space-y-4">
                <h3 className="text-sm font-semibold">PR #{impact.pr_number}</h3>

                {/* Risk Score */}
                <div>
                  <p className="text-xs text-text-muted mb-1">Risk Score</p>
                  <div className="flex items-center gap-2">
                    <div className="h-3 flex-1 rounded-full bg-gray-200">
                      <div
                        className={`h-3 rounded-full ${
                          impact.risk_score >= 0.7
                            ? "bg-red-500"
                            : impact.risk_score >= 0.4
                            ? "bg-amber-500"
                            : "bg-green-500"
                        }`}
                        style={{ width: `${impact.risk_score * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-mono font-bold">
                      {(impact.risk_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                <div>
                  <p className="text-xs text-text-muted">Related Defects</p>
                  <p className="text-lg font-bold">{impact.related_defects}</p>
                </div>

                <div>
                  <p className="text-xs text-text-muted mb-1">Affected Features</p>
                  <div className="flex flex-wrap gap-1">
                    {impact.affected_features.length > 0 ? (
                      impact.affected_features.map((f) => (
                        <Badge key={f} variant="info">{f}</Badge>
                      ))
                    ) : (
                      <span className="text-sm text-text-muted">None identified</span>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <EmptyState message="Impact data unavailable" />
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
