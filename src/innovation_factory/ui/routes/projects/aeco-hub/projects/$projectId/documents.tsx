import { createFileRoute, useParams } from "@tanstack/react-router";
import { Suspense, useState } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { useAeco_listDocumentsSuspense } from "@/lib/api";
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
import { FileText } from "lucide-react";

export const Route = createFileRoute("/projects/aeco-hub/projects/$projectId/documents")({
  component: () => <DocumentsPage />,
});

function DocumentsPage() {
  const { projectId } = useParams({ from: "/projects/aeco-hub/projects/$projectId/documents" });
  const pid = Number(projectId);
  const [phaseFilter, setPhaseFilter] = useState<string>("");

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h2 className="text-lg font-semibold flex-1">Document library</h2>
        <Select
          value={phaseFilter || "all"}
          onValueChange={(v) => setPhaseFilter(v === "all" ? "" : v)}
        >
          <SelectTrigger className="w-44">
            <SelectValue placeholder="All phases" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All phases</SelectItem>
            <SelectItem value="design">Design</SelectItem>
            <SelectItem value="build">Build</SelectItem>
            <SelectItem value="operate">Operate</SelectItem>
            <SelectItem value="demolish">Demolish</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={() => (
              <Card>
                <CardContent className="p-6 text-destructive">
                  Failed to load documents.
                </CardContent>
              </Card>
            )}
          >
            <Suspense fallback={<TableSkeleton />}>
              <DocumentTable pid={pid} phaseFilter={phaseFilter} />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

function DocumentTable({ pid, phaseFilter }: { pid: number; phaseFilter: string }) {
  const { data: docs } = useAeco_listDocumentsSuspense({
    params: {
      project_id: pid,
      ...(phaseFilter ? { phase: phaseFilter as never } : {}),
    },
    ...selector(),
  });

  if (docs.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-muted-foreground">
          No documents match this filter.
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
              <TableHead>Type</TableHead>
              <TableHead>Phase</TableHead>
              <TableHead>Author</TableHead>
              <TableHead>Version</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {docs.map((doc) => (
              <TableRow key={doc.id}>
                <TableCell className="font-medium flex items-center gap-2">
                  <FileText size={14} className="text-muted-foreground" />
                  {doc.title}
                </TableCell>
                <TableCell className="capitalize text-sm">
                  {doc.document_type.replace(/_/g, " ")}
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-xs capitalize">
                    {doc.phase}
                  </Badge>
                </TableCell>
                <TableCell className="text-sm">{doc.author}</TableCell>
                <TableCell className="text-sm">{doc.version}</TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {new Date(doc.created_at).toLocaleDateString()}
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
