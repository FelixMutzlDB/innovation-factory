import { createFileRoute, useParams } from "@tanstack/react-router";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import {
  useAeco_listBimModelsSuspense,
  useAeco_listClashReportsSuspense,
  useAeco_listRoomRequirementsSuspense,
} from "@/lib/api";
import { selector } from "@/lib/selector";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { FileBox, AlertTriangle, ClipboardCheck } from "lucide-react";

export const Route = createFileRoute("/projects/aeco-hub/projects/$projectId/design")({
  component: () => <DesignPage />,
});

const SEVERITY_COLOR: Record<string, string> = {
  minor: "bg-slate-500/15 text-slate-600 border-slate-500/30",
  moderate: "bg-blue-500/15 text-blue-600 border-blue-500/30",
  major: "bg-amber-500/15 text-amber-600 border-amber-500/30",
  critical: "bg-red-500/15 text-red-600 border-red-500/30",
};

function DesignPage() {
  const { projectId } = useParams({ from: "/projects/aeco-hub/projects/$projectId/design" });
  const pid = Number(projectId);

  return (
    <div className="space-y-6">
      <Section title="BIM models" icon={<FileBox size={16} />}>
        <QueryErrorResetBoundary>
          {({ reset }) => (
            <ErrorBoundary onReset={reset} fallbackRender={SimpleErr}>
              <Suspense fallback={<RowSkeleton />}>
                <BimModelsTable pid={pid} />
              </Suspense>
            </ErrorBoundary>
          )}
        </QueryErrorResetBoundary>
      </Section>

      <Section title="Clash reports" icon={<AlertTriangle size={16} />}>
        <QueryErrorResetBoundary>
          {({ reset }) => (
            <ErrorBoundary onReset={reset} fallbackRender={SimpleErr}>
              <Suspense fallback={<RowSkeleton />}>
                <ClashesTable pid={pid} />
              </Suspense>
            </ErrorBoundary>
          )}
        </QueryErrorResetBoundary>
      </Section>

      <Section title="Room requirements" icon={<ClipboardCheck size={16} />}>
        <QueryErrorResetBoundary>
          {({ reset }) => (
            <ErrorBoundary onReset={reset} fallbackRender={SimpleErr}>
              <Suspense fallback={<RowSkeleton />}>
                <RequirementsTable pid={pid} />
              </Suspense>
            </ErrorBoundary>
          )}
        </QueryErrorResetBoundary>
      </Section>
    </div>
  );
}

function Section({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">{children}</CardContent>
    </Card>
  );
}

function BimModelsTable({ pid }: { pid: number }) {
  const { data: models } = useAeco_listBimModelsSuspense({
    params: { project_id: pid },
    ...selector(),
  });
  if (models.length === 0) return <Empty msg="No BIM models for this project yet." />;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Model</TableHead>
          <TableHead>Discipline</TableHead>
          <TableHead>LOD</TableHead>
          <TableHead>Version</TableHead>
          <TableHead>Size (MB)</TableHead>
          <TableHead>Elements</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {models.map((m) => (
          <TableRow key={m.id}>
            <TableCell className="font-medium">{m.name}</TableCell>
            <TableCell className="capitalize text-sm">{m.discipline}</TableCell>
            <TableCell className="text-sm">{m.lod}</TableCell>
            <TableCell className="text-sm">{m.version}</TableCell>
            <TableCell className="text-sm">{m.file_size_mb}</TableCell>
            <TableCell className="text-sm">{m.element_count.toLocaleString()}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function ClashesTable({ pid }: { pid: number }) {
  const { data: clashes } = useAeco_listClashReportsSuspense({
    params: { project_id: pid },
    ...selector(),
  });
  if (clashes.length === 0) return <Empty msg="No clashes detected." />;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Title</TableHead>
          <TableHead>Disciplines</TableHead>
          <TableHead>Clashes</TableHead>
          <TableHead>Severity</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {clashes.map((c) => (
          <TableRow key={c.id}>
            <TableCell className="font-medium">{c.title}</TableCell>
            <TableCell className="text-sm capitalize">
              {c.discipline_a} ↔ {c.discipline_b}
            </TableCell>
            <TableCell className="text-sm">{c.clash_count}</TableCell>
            <TableCell>
              <Badge variant="outline" className={`text-xs capitalize ${SEVERITY_COLOR[c.severity] ?? ""}`}>
                {c.severity}
              </Badge>
            </TableCell>
            <TableCell className="text-sm capitalize">{c.status.replace(/_/g, " ")}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function RequirementsTable({ pid }: { pid: number }) {
  const { data: reqs } = useAeco_listRoomRequirementsSuspense({
    params: { project_id: pid, limit: 50 },
    ...selector(),
  });
  if (reqs.length === 0) return <Empty msg="No room requirements." />;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Requirement</TableHead>
          <TableHead>Spec</TableHead>
          <TableHead>Description</TableHead>
          <TableHead>Met</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {reqs.map((r) => (
          <TableRow key={r.id}>
            <TableCell className="font-medium">{r.requirement_type}</TableCell>
            <TableCell className="text-sm">
              {r.spec_value} {r.spec_unit}
            </TableCell>
            <TableCell className="text-sm text-muted-foreground max-w-md truncate">
              {r.description}
            </TableCell>
            <TableCell>
              <Badge
                variant="outline"
                className={
                  r.is_met
                    ? "bg-green-500/15 text-green-600 border-green-500/30 text-xs"
                    : "bg-red-500/15 text-red-600 border-red-500/30 text-xs"
                }
              >
                {r.is_met ? "Yes" : "No"}
              </Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function Empty({ msg }: { msg: string }) {
  return <div className="p-6 text-center text-sm text-muted-foreground">{msg}</div>;
}

function SimpleErr() {
  return <div className="p-6 text-destructive text-sm">Failed to load.</div>;
}

function RowSkeleton() {
  return (
    <div className="p-4 space-y-2">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-8 w-full" />
      ))}
    </div>
  );
}
