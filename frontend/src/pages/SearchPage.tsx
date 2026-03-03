import { useState } from "react";
import { jiraApi, ragApi } from "@/api/client";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Select } from "@/components/ui/Input";
import { Badge, StatusBadge } from "@/components/ui/Badge";
import { Table, Thead, Th, Td, Tr } from "@/components/ui/Table";
import { EmptyState, ErrorMessage } from "@/components/ui/Spinner";
import { Search, Copy, Sparkles } from "lucide-react";
import type { JiraIssue, SimilarityResult, DuplicateResult } from "@/types";

type SearchMode = "jira" | "similarity" | "duplicates";

export default function SearchPage() {
  const [mode, setMode] = useState<SearchMode>("jira");
  const [query, setQuery] = useState("");
  const [issueType, setIssueType] = useState("");
  const [threshold, setThreshold] = useState(0.85);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const [jiraResults, setJiraResults] = useState<JiraIssue[]>([]);
  const [similarResults, setSimilarResults] = useState<SimilarityResult[]>([]);
  const [dupeResults, setDupeResults] = useState<DuplicateResult[]>([]);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setIsLoading(true);
    setError("");
    try {
      if (mode === "jira") {
        const results = await jiraApi.search(query, issueType || undefined);
        setJiraResults(results);
      } else if (mode === "similarity") {
        const results = await ragApi.similarity(query);
        setSimilarResults(results);
      } else {
        const results = await ragApi.duplicates(query, threshold);
        setDupeResults(results);
      }
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Search failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Search & Discovery</h1>

      {/* Search Controls */}
      <Card>
        <div className="flex gap-2 mb-4">
          {(["jira", "similarity", "duplicates"] as SearchMode[]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                mode === m
                  ? "bg-primary-600 text-white"
                  : "bg-surface-secondary text-text-secondary hover:bg-surface-hover"
              }`}
            >
              {m === "jira" && <><Search size={14} className="inline mr-1" /> Jira Search</>}
              {m === "similarity" && <><Sparkles size={14} className="inline mr-1" /> Similarity</>}
              {m === "duplicates" && <><Copy size={14} className="inline mr-1" /> Duplicates</>}
            </button>
          ))}
        </div>

        <div className="flex gap-3">
          <div className="flex-1">
            <Input
              placeholder={
                mode === "jira"
                  ? "Search Jira issues..."
                  : mode === "similarity"
                  ? "Describe the issue to find similar ones..."
                  : "Paste bug summary to check for duplicates..."
              }
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
          </div>
          {mode === "jira" && (
            <Select
              options={[
                { value: "", label: "All Types" },
                { value: "defect", label: "Defect" },
                { value: "story", label: "Story" },
                { value: "task", label: "Task" },
                { value: "epic", label: "Epic" },
              ]}
              value={issueType}
              onChange={(e) => setIssueType(e.target.value)}
              className="w-36"
            />
          )}
          {mode === "duplicates" && (
            <Input
              type="number"
              min={0}
              max={1}
              step={0.05}
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="w-24"
              placeholder="Threshold"
            />
          )}
          <Button onClick={handleSearch} isLoading={isLoading}>
            Search
          </Button>
        </div>
      </Card>

      {error && <ErrorMessage message={error} />}

      {/* Jira Results */}
      {mode === "jira" && jiraResults.length > 0 && (
        <Card padding={false}>
          <div className="p-4 border-b border-border">
            <CardTitle>Jira Issues ({jiraResults.length})</CardTitle>
          </div>
          <Table>
            <Thead>
              <tr>
                <Th>Key</Th>
                <Th>Type</Th>
                <Th>Summary</Th>
                <Th>Status</Th>
                <Th>Priority</Th>
                <Th>Assignee</Th>
                <Th>Reopens</Th>
              </tr>
            </Thead>
            <tbody>
              {jiraResults.map((issue) => (
                <Tr key={issue.jira_key}>
                  <Td className="font-mono text-xs font-medium">{issue.jira_key}</Td>
                  <Td>
                    <Badge variant={issue.issue_type === "defect" ? "danger" : "neutral"}>
                      {issue.issue_type}
                    </Badge>
                  </Td>
                  <Td className="max-w-[300px] truncate">{issue.summary}</Td>
                  <Td><StatusBadge status={issue.status} /></Td>
                  <Td>{issue.priority || "-"}</Td>
                  <Td className="text-xs">{issue.assignee_email || "-"}</Td>
                  <Td>
                    {issue.reopen_count > 0 ? (
                      <Badge variant="warning">{issue.reopen_count}</Badge>
                    ) : (
                      "0"
                    )}
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}

      {/* Similarity Results */}
      {mode === "similarity" && similarResults.length > 0 && (
        <Card padding={false}>
          <div className="p-4 border-b border-border">
            <CardTitle>Similar Issues ({similarResults.length})</CardTitle>
          </div>
          <Table>
            <Thead>
              <tr>
                <Th>Key</Th>
                <Th>Type</Th>
                <Th>Summary</Th>
                <Th>Similarity</Th>
              </tr>
            </Thead>
            <tbody>
              {similarResults.map((r) => (
                <Tr key={r.jira_key}>
                  <Td className="font-mono text-xs">{r.jira_key}</Td>
                  <Td><Badge>{r.issue_type}</Badge></Td>
                  <Td className="max-w-[400px] truncate">{r.summary}</Td>
                  <Td>
                    <ScoreBar score={r.score} />
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}

      {/* Duplicate Results */}
      {mode === "duplicates" && dupeResults.length > 0 && (
        <Card padding={false}>
          <div className="p-4 border-b border-border">
            <CardTitle>Duplicate Check ({dupeResults.length})</CardTitle>
          </div>
          <Table>
            <Thead>
              <tr>
                <Th>Key</Th>
                <Th>Summary</Th>
                <Th>Similarity</Th>
                <Th>Duplicate?</Th>
              </tr>
            </Thead>
            <tbody>
              {dupeResults.map((r) => (
                <Tr key={r.jira_key}>
                  <Td className="font-mono text-xs">{r.jira_key}</Td>
                  <Td className="max-w-[400px] truncate">{r.summary}</Td>
                  <Td><ScoreBar score={r.similarity} /></Td>
                  <Td>
                    {r.is_duplicate ? (
                      <Badge variant="danger">Likely Duplicate</Badge>
                    ) : (
                      <Badge variant="success">Unique</Badge>
                    )}
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}

      {!isLoading && !error && mode === "jira" && jiraResults.length === 0 && query && (
        <EmptyState message="No results found. Try a different search query." />
      )}
    </div>
  );
}

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = pct >= 85 ? "bg-red-500" : pct >= 60 ? "bg-amber-500" : "bg-green-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-20 rounded-full bg-gray-200">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono">{pct}%</span>
    </div>
  );
}
