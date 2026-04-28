import { createFileRoute, useParams } from "@tanstack/react-router";
import { Suspense, useState } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { useAeco_listIssuesSuspense } from "@/lib/api";
import { selector } from "@/lib/selector";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export const Route = createFileRoute("/projects/aeco-hub/projects/$projectId/issues")({
  component: () => <IssuesPage />,
});

const SEVERITY_COLOR: Record<string, string> = {
  minor: "bg-slate-500/15 text-slate-600 border-slate-500/30",
  moderate: "bg-blue-500/15 text-blue-600 border-blue-500/30",
  major: "bg-amber-500/15 text-amber-600 border-amber-500/30",
  critical: "bg-red-500/15 text-red-600 border-red-500/30",
};

const STATUS_COLOR: Record<string, string> = {
  open: "bg-amber-500/15 text-amber-600 border-amber-500/30",
  in_review: "bg-blue-500/15 text-blue-600 border-blue-500/30",
  in_progress: "bg-purple-500/15 text-purple-600 border-purple-500/30",
  resolved: "bg-green-500/15 text-green-600 border-green-500/30",
  closed: "bg-slate-500/15 text-slate-600 border-slate-500/30",
};

function IssuesPage() {
  const { projectId } = useParams({ from: "/projects/aeco-hub/projects/$projectId/issues" });
  const pid = Number(projectId);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [severityFilter, setSeverityFilter] = useState<string>("");

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h2 className="text-lg font-semibold flex-1">Issue tracker</h2>
        <Select
          value={statusFilter || "all"}
          onValueChange={(v) => setStatusFilter(v === "all" ? "" : v)}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="open">Open</SelectItem>
            <SelectItem value="in_review">In review</SelectItem>
            <SelectItem value="in_progress">In progress</SelectItem>
            <SelectItem value="resolved">Resolved</SelectItem>
            <SelectItem value="closed">Closed</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={severityFilter || "all"}
          onValueChange={(v) => setSeverityFilter(v === "all" ? "" : v)}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All severities" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All severities</SelectItem>
            <SelectItem value="minor">Minor</SelectItem>
            <SelectItem value="moderate">Moderate</SelectItem>
            <SelectItem value="major">Major</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={() => (
              <Card>
                <CardContent className="p-6 text-destructive">Failed to load issues.</CardContent>
              </Card>
            )}
          >
            <Suspense fallback={<TableSkeleton />}>
              <IssueTable
                pid={pid}
                statusFilter={statusFilter}
                severityFilter={severityFilter}
              />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

function IssueTable({
  pid,
  statusFilter,
  severityFilter,
}: {
  pid: number;
  statusFilter: string;
  severityFilter: string;
}) {
  const { data: issues } = useAeco_listIssuesSuspense({
    params: {
      project_id: pid,
      ...(statusFilter ? { status: statusFilter as never } : {}),
      ...(severityFilter ? { severity: severityFilter as never } : {}),
    },
    ...selector(),
  });

  if (issues.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-muted-foreground">
          No issues match these filters.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Assigned</TableHead>
              <TableHead>Raised</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {issues.map((issue) => (
              <TableRow key={issue.id}>
                <TableCell className="font-medium max-w-md truncate">{issue.title}</TableCell>
                <TableCell className="capitalize text-sm text-muted-foreground">
                  {issue.category.replace(/_/g, " ")}
                </TableCell>
                <TableCell>
                  <Badge
                    variant="outline"
                    className={`text-xs capitalize ${SEVERITY_COLOR[issue.severity] ?? ""}`}
                  >
                    {issue.severity}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge
                    variant="outline"
                    className={`text-xs ${STATUS_COLOR[issue.status] ?? ""}`}
                  >
                    {issue.status.replace(/_/g, " ")}
                  </Badge>
                </TableCell>
                <TableCell className="text-sm">{issue.assigned_to ?? "—"}</TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {new Date(issue.created_at).toLocaleDateString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function TableSkeleton() {
  return (
    <Card>
      <CardContent className="p-4 space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </CardContent>
    </Card>
  );
}
